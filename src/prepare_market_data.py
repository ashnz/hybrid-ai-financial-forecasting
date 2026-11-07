
# Prepare Processed Market Dataset
# Hybrid AI Financial Forecasting System

from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

import pandas as pd
import yaml
from pandas.testing import assert_frame_equal

from src.cleaning_rules import apply_cleaning_policy


ROOT = Path(__file__).resolve().parents[1]

SNAPSHOT_ID = "20261107T082129_328387Z"

RAW_DIR = ROOT / "data" / "raw" / SNAPSHOT_ID
PROCESSED_DIR = ROOT / "data" / "processed" / SNAPSHOT_ID

CONFIG_PATH = ROOT / "config" / "project.yaml"

with CONFIG_PATH.open("r", encoding="utf-8") as file:
    config = yaml.safe_load(file)

TICKERS = list(dict.fromkeys(
    config["market"]["stocks"]
    + [config["market"]["benchmark"]]
))

ORIGINAL_COLUMNS = [
    "Ticker", "Date",
    "Open", "High", "Low", "Close",
    "Adj Close", "Volume",
    "Dividends", "Stock Splits"
]


# -----------------------------------------
# 1. File integrity utilities
# -----------------------------------------

def calculate_hash(path):
    digest = hashlib.sha256()

    with path.open("rb") as file:
        for block in iter(
            lambda: file.read(1024 * 1024), b""
        ):
            digest.update(block)

    return digest.hexdigest()


def verify_original_values(raw, processed, symbol):
    """Confirm that processing preserved source data."""

    for column in raw.columns:

        if column not in processed.columns:
            raise ValueError(
                f"{symbol}: Missing original column {column}"
            )

    # Compare timestamps as identical UTC instants.
    raw_dates = pd.to_datetime(
        raw["Date"], utc=True
    ).astype("datetime64[ns, UTC]")

    processed_dates = pd.to_datetime(
        processed["Date"], utc=True
    ).astype("datetime64[ns, UTC]")

    assert raw_dates.reset_index(drop=True).equals(
        processed_dates.reset_index(drop=True)
    ), f"{symbol}: Dates changed during processing"

    # Compare all original non-date columns.
    columns = [
        column for column in raw.columns
        if column != "Date"
    ]

    assert_frame_equal(
        raw[columns].reset_index(drop=True),
        processed[columns].reset_index(drop=True),
        check_dtype=True,
        check_exact=True
    )


# -----------------------------------------
# 2. Load the verified source snapshot
# -----------------------------------------

def load_raw_datasets():

    manifest_path = RAW_DIR / "manifest.json"

    with manifest_path.open(
        "r", encoding="utf-8"
    ) as file:
        manifest = json.load(file)

    if manifest["snapshot_id"] != SNAPSHOT_ID:
        raise ValueError("Raw snapshot ID mismatch")

    records = {
        item["ticker"]: item
        for item in manifest["files"]
    }

    if set(records) != set(TICKERS):
        raise ValueError(
            "Snapshot ticker universe does not match config"
        )

    datasets = {}

    for symbol in TICKERS:

        record = records[symbol]
        path = RAW_DIR / record["file"]

        if calculate_hash(path) != record["sha256"]:
            raise ValueError(
                f"{symbol}: Raw file hash mismatch"
            )

        df = pd.read_parquet(path)

        if len(df) != record["rows"]:
            raise ValueError(
                f"{symbol}: Raw row count mismatch"
            )

        datasets[symbol] = df

    return datasets, manifest


# -----------------------------------------
# 3. Create processed datasets
# -----------------------------------------

def main():

    print("=" * 60)
    print("PROCESSED MARKET DATA PREPARATION")
    print("=" * 60)

    datasets, source_manifest = load_raw_datasets()

    # Prevent accidentally overwriting an existing run.
    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=False
    )

    records = []
    summaries = []

    for symbol, raw in datasets.items():

        processed, summary = apply_cleaning_policy(
            symbol, raw
        )

        # Reject statuses must be resolved before export.
        if summary["Reject"] > 0:
            raise ValueError(
                f"{symbol}: Rejected observations require review"
            )

        if len(processed) != len(raw):
            raise ValueError(
                f"{symbol}: Row count changed"
            )

        # Verify that original market values are intact.
        verify_original_values(
            raw, processed, symbol
        )

        output = (
            PROCESSED_DIR / f"{symbol}_processed.parquet"
        )

        processed.to_parquet(
            output,
            engine="pyarrow",
            index=False
        )

        # Reload and verify the saved file.
        restored = pd.read_parquet(output)

        verify_original_values(
            raw, restored, symbol
        )

        if not (
            processed["Quality_Status"]
            .reset_index(drop=True)
            .equals(
                restored["Quality_Status"]
                .reset_index(drop=True)
            )
        ):
            raise ValueError(
                f"{symbol}: Quality statuses changed"
            )

        records.append({
            "ticker": symbol,
            "file": output.name,
            "rows": len(restored),
            "sha256": calculate_hash(output),
            "quality_counts": {
                "KEEP": summary["Keep"],
                "REVIEW": summary["Review"],
                "REJECT": summary["Reject"]
            }
        })

        summaries.append(summary)

        print(
            f"{symbol}: "
            f"Rows={len(restored)}, "
            f"KEEP={summary['Keep']}, "
            f"REVIEW={summary['Review']}, "
            f"REJECT={summary['Reject']}"
        )

    manifest = {
        "source_snapshot": SNAPSHOT_ID,
        "source_manifest_hash": calculate_hash(
            RAW_DIR / "manifest.json"
        ),
        "created_at_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "status": "candidate_pending_final_validation",
        "policy": "src/cleaning_rules.py",
        "original_market_values_modified": False,
        "files": records
    }

    manifest_path = (
        PROCESSED_DIR / "processing_manifest.json"
    )

    manifest_path.write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8"
    )

    summary_df = pd.DataFrame(summaries)

    print("\n" + "=" * 60)
    print("PROCESSING SUMMARY")
    print("=" * 60)

    print(summary_df.to_string(index=False))

    print(
        "\nTotal processed rows:",
        int(summary_df["Total_Rows"].sum())
    )

    print("Original market values: PRESERVED")
    print("Processed datasets: VERIFIED")
    print("Status: CANDIDATE - FINAL VALIDATION PENDING")

    print("\nSaved to:", PROCESSED_DIR)


if __name__ == "__main__":
    main()
