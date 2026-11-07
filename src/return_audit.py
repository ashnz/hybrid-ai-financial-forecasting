
# Historical Return and Corporate Action Audit

from pathlib import Path
import hashlib
import json

import numpy as np
import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]

SNAPSHOT_ID = "20261107T082129_328387Z"

SNAPSHOT_DIR = ROOT / "data" / "raw" / SNAPSHOT_ID
REPORT_DIR = ROOT / "reports"

REPORT_DIR.mkdir(parents=True, exist_ok=True)

with (ROOT / "config" / "project.yaml").open(
    "r", encoding="utf-8"
) as file:
    config = yaml.safe_load(file)

TICKERS = list(dict.fromkeys(
    config["market"]["stocks"]
    + [config["market"]["benchmark"]]
))

# Exploratory screening thresholds
LARGE_RETURN_THRESHOLD = 0.20
ROBUST_Z_THRESHOLD = 8.0


# ------------------------------------------
# 1. Verify the snapshot
# ------------------------------------------

def file_hash(path):
    digest = hashlib.sha256()

    with path.open("rb") as file:
        for block in iter(
            lambda: file.read(1024 * 1024), b""
        ):
            digest.update(block)

    return digest.hexdigest()


def load_snapshot():
    manifest_path = SNAPSHOT_DIR / "manifest.json"

    with manifest_path.open(
        "r", encoding="utf-8"
    ) as file:
        manifest = json.load(file)

    if manifest["snapshot_id"] != SNAPSHOT_ID:
        raise ValueError("Snapshot ID mismatch")

    records = {
        r["ticker"]: r
        for r in manifest["files"]
    }

    datasets = {}

    for symbol in TICKERS:
        record = records[symbol]

        path = SNAPSHOT_DIR / record["file"]

        if file_hash(path) != record["sha256"]:
            raise ValueError(
                f"{symbol}: SHA-256 mismatch"
            )

        df = pd.read_parquet(path)

        if len(df) != record["rows"]:
            raise ValueError(
                f"{symbol}: Row count mismatch"
            )

        df = df.sort_values("Date").copy()

        datasets[symbol] = df.reset_index(drop=True)

    return datasets


# ------------------------------------------
# 2. Calculate return statistics
# ------------------------------------------

def analyse_returns(symbol, df):
    data = df.copy()

    prices = data["Adj Close"]

    if prices.isna().any() or (prices <= 0).any():
        raise ValueError(
            f"{symbol}: Invalid adjusted prices"
        )

    # Simple percentage returns
    data["Adjusted_Return"] = (
        prices.pct_change(fill_method=None)
    )

    data["Close_Return"] = (
        data["Close"].pct_change(fill_method=None)
    )

    # Logarithmic returns
    data["Log_Return"] = np.log(
        prices / prices.shift(1)
    )

    # Difference between price-return definitions
    data["Return_Difference"] = (
        data["Adjusted_Return"]
        - data["Close_Return"]
    )

    returns = data["Adjusted_Return"].dropna()

    median_return = returns.median()

    mad = np.median(
        np.abs(returns - median_return)
    )

    # Robust anomaly score
    if mad > 0:
        data["Robust_Z"] = (
            0.6745
            * (data["Adjusted_Return"] - median_return)
            / mad
        )
    else:
        data["Robust_Z"] = np.nan

    # Screening flags
    data["Large_Return"] = (
        data["Adjusted_Return"].abs()
        >= LARGE_RETURN_THRESHOLD
    )

    data["Statistical_Outlier"] = (
        data["Robust_Z"].abs()
        > ROBUST_Z_THRESHOLD
    )

    data["Flagged"] = (
        data["Large_Return"]
        | data["Statistical_Outlier"]
    )

    # Corporate actions
    data["Dividend_Event"] = (
        data["Dividends"].fillna(0) != 0
    )

    data["Split_Event"] = (
        data["Stock Splits"].fillna(0) != 0
    )

    data["Ticker"] = symbol

    # Summary statistics
    summary = {
        "Ticker": symbol,
        "Observations": len(data),
        "Mean_Daily_Return_Pct": (
            returns.mean() * 100
        ),
        "Daily_Volatility_Pct": (
            returns.std() * 100
        ),
        "Minimum_Return_Pct": (
            returns.min() * 100
        ),
        "Maximum_Return_Pct": (
            returns.max() * 100
        ),
        "Large_Return_Events": int(
            data["Large_Return"].sum()
        ),
        "Statistical_Outliers": int(
            data["Statistical_Outlier"].sum()
        ),
        "Total_Flagged_Rows": int(
            data["Flagged"].sum()
        ),
        "Dividend_Events": int(
            data["Dividend_Event"].sum()
        ),
        "Split_Events": int(
            data["Split_Event"].sum()
        ),
    }

    return data, summary


# ------------------------------------------
# 3. Main analysis
# ------------------------------------------

def main():
    print("=" * 60)
    print("RETURN AND CORPORATE ACTION AUDIT")
    print("=" * 60)

    datasets = load_snapshot()

    summaries = []
    flagged_rows = []
    corporate_events = []

    for symbol, df in datasets.items():
        analysed, summary = analyse_returns(
            symbol, df
        )

        summaries.append(summary)

        flags = analysed.loc[
            analysed["Flagged"]
        ].copy()

        flagged_rows.append(flags)

        actions = analysed.loc[
            analysed["Dividend_Event"]
            | analysed["Split_Event"]
        ].copy()

        corporate_events.append(actions)

        print(f"\n{symbol}")
        print(
            "Mean daily return:",
            f"{summary['Mean_Daily_Return_Pct']:.4f}%"
        )
        print(
            "Daily volatility:",
            f"{summary['Daily_Volatility_Pct']:.4f}%"
        )
        print(
            "Largest daily increase:",
            f"{summary['Maximum_Return_Pct']:.2f}%"
        )
        print(
            "Largest daily decrease:",
            f"{summary['Minimum_Return_Pct']:.2f}%"
        )
        print(
            "Flagged observations:",
            summary["Total_Flagged_Rows"]
        )
        print(
            "Corporate-action events:",
            len(actions)
        )

        if not flags.empty:
            print("\nMost extreme flagged returns:")

            top = flags.assign(
                Absolute_Return=flags[
                    "Adjusted_Return"
                ].abs()
            ).nlargest(
                5, "Absolute_Return"
            )

            print(
                top[[
                    "Date",
                    "Adjusted_Return",
                    "Robust_Z",
                    "Dividend_Event",
                    "Split_Event",
                ]].to_string(index=False)
            )

    # --------------------------------------
    # 4. Export audit reports
    # --------------------------------------

    summary_df = pd.DataFrame(summaries)

    flagged_df = pd.concat(
        flagged_rows,
        ignore_index=True
    )

    actions_df = pd.concat(
        corporate_events,
        ignore_index=True
    )

    summary_df.to_csv(
        REPORT_DIR / "return_audit_summary.csv",
        index=False
    )

    flagged_df.to_csv(
        REPORT_DIR / "return_audit_flags.csv",
        index=False
    )

    actions_df.to_csv(
        REPORT_DIR / "corporate_actions.csv",
        index=False
    )

    print("\n" + "=" * 60)
    print("AUDIT SUMMARY")
    print("=" * 60)

    print(summary_df.to_string(index=False))

    print("\nTotal flagged rows:", len(flagged_df))
    print("Corporate-action rows:", len(actions_df))

    print("\nReports saved to:", REPORT_DIR)
    print("RAW DATA: UNCHANGED")
    print("RETURN AUDIT: COMPLETED")


if __name__ == "__main__":
    main()
