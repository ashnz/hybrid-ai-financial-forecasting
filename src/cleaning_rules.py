
# Financial Data Cleaning Policy
# Hybrid AI Financial Forecasting System

from pathlib import Path
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

PRICE_COLUMNS = [
    "Open", "High", "Low", "Close", "Adj Close"
]

LARGE_RETURN_THRESHOLD = 0.20
ROBUST_Z_THRESHOLD = 8.0


def apply_cleaning_policy(symbol, df):
    """Classify rows without modifying market observations."""

    data = df.copy()

    required = [
        "Date", *PRICE_COLUMNS, "Volume"
    ]

    missing_columns = set(required) - set(data.columns)

    if missing_columns:
        raise ValueError(
            f"{symbol}: Missing columns {missing_columns}"
        )

    # Structural and price validity
    missing_values = data[required].isna().any(axis=1)

    invalid_prices = data[
        PRICE_COLUMNS
    ].le(0).any(axis=1)

    negative_volume = data["Volume"].lt(0)

    complete_ohlc = data[
        ["Open", "High", "Low", "Close"]
    ].notna().all(axis=1)

    inconsistent_ohlc = complete_ohlc & (
        (data["High"] < data["Low"])
        | (data["Open"] > data["High"])
        | (data["Open"] < data["Low"])
        | (data["Close"] > data["High"])
        | (data["Close"] < data["Low"])
    )

    duplicate_dates = data["Date"].duplicated(
        keep=False
    )

    zero_volume = data["Volume"].eq(0)

    # Retrospective return audit
    returns = data["Adj Close"].pct_change(
        fill_method=None
    )

    valid_returns = returns.replace(
        [np.inf, -np.inf], np.nan
    ).dropna()

    median_return = valid_returns.median()

    mad = np.median(
        np.abs(valid_returns - median_return)
    )

    if mad > 0:
        robust_z = (
            0.6745 * (returns - median_return) / mad
        )
    else:
        robust_z = pd.Series(
            np.nan, index=data.index
        )

    unusual_return = (
        returns.abs().ge(LARGE_RETURN_THRESHOLD)
        | robust_z.abs().gt(ROBUST_Z_THRESHOLD)
    )

    # Apply classification rules
    reject = (
        missing_values
        | invalid_prices
        | negative_volume
        | inconsistent_ohlc
    )

    review = (
        duplicate_dates
        | zero_volume
        | unusual_return
    ) & ~reject

    data["Quality_Status"] = np.select(
        [reject, review],
        ["REJECT", "REVIEW"],
        default="KEEP"
    )

    # Record reasons for flagged rows
    flags = {
        "Missing_Value": missing_values,
        "Invalid_Price": invalid_prices,
        "Negative_Volume": negative_volume,
        "Inconsistent_OHLC": inconsistent_ohlc,
        "Duplicate_Date": duplicate_dates,
        "Zero_Volume": zero_volume,
        "Unusual_Return": unusual_return,
    }

    for name, mask in flags.items():
        data[name] = mask

    data["Ticker"] = symbol

    summary = {
        "Ticker": symbol,
        "Total_Rows": len(data),
        "Keep": int(
            (data["Quality_Status"] == "KEEP").sum()
        ),
        "Review": int(
            (data["Quality_Status"] == "REVIEW").sum()
        ),
        "Reject": int(
            (data["Quality_Status"] == "REJECT").sum()
        ),
    }

    return data, summary


def main():

    print("=" * 60)
    print("FINANCIAL DATA CLEANING POLICY")
    print("=" * 60)

    manifest_path = SNAPSHOT_DIR / "manifest.json"

    with manifest_path.open(
        "r", encoding="utf-8"
    ) as file:
        manifest = json.load(file)

    records = {
        record["ticker"]: record
        for record in manifest["files"]
    }

    summaries = []
    review_records = []

    for symbol in TICKERS:

        path = SNAPSHOT_DIR / records[symbol]["file"]

        df = pd.read_parquet(path)

        classified, summary = apply_cleaning_policy(
            symbol, df
        )

        summaries.append(summary)

        flagged = classified.loc[
            classified["Quality_Status"] != "KEEP"
        ].copy()

        review_records.append(flagged)

        print(
            f"{symbol}: "
            f"KEEP={summary['Keep']}, "
            f"REVIEW={summary['Review']}, "
            f"REJECT={summary['Reject']}"
        )

    summary_df = pd.DataFrame(summaries)

    flagged_df = pd.concat(
        review_records,
        ignore_index=True
    )

    summary_df.to_csv(
        REPORT_DIR / "cleaning_policy_summary.csv",
        index=False
    )

    flagged_df.to_csv(
        REPORT_DIR / "cleaning_policy_flags.csv",
        index=False
    )

    print("\n" + "=" * 60)
    print("CLEANING POLICY SUMMARY")
    print("=" * 60)

    print(summary_df.to_string(index=False))

    print("\nFlagged rows:", len(flagged_df))
    print("Raw datasets: UNCHANGED")
    print("No observations removed")
    print("CLEANING POLICY AUDIT: COMPLETED")


if __name__ == "__main__":
    main()
