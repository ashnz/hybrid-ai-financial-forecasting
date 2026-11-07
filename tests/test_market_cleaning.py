
# Automated Tests for Market Data Cleaning

from pathlib import Path
import hashlib
import json

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from src.cleaning_rules import apply_cleaning_policy


ROOT = Path(__file__).resolve().parents[1]

SNAPSHOT_ID = "20261107T082129_328387Z"

RAW_DIR = ROOT / "data" / "raw" / SNAPSHOT_ID
PROCESSED_DIR = (
    ROOT / "data" / "processed" / SNAPSHOT_ID
)


# ---------------------------------------------
# 1. Create controlled test observations
# ---------------------------------------------

@pytest.fixture
def sample_data():

    dates = pd.date_range(
        "2026-01-05",
        periods=30,
        freq="B",
        tz="America/New_York"
    )

    closes = [100.0 + i * 0.1 for i in range(30)]

    return pd.DataFrame({
        "Ticker": ["TEST"] * 30,
        "Date": dates,
        "Open": closes,
        "High": [v + 1 for v in closes],
        "Low": [v - 1 for v in closes],
        "Close": closes,
        "Adj Close": closes,
        "Volume": [1000000] * 30,
        "Dividends": [0.0] * 30,
        "Stock Splits": [0.0] * 30,
    })


# ---------------------------------------------
# 2. Unit tests for the cleaning rules
# ---------------------------------------------

def test_valid_data_is_kept(sample_data):

    result, summary = apply_cleaning_policy(
        "TEST", sample_data
    )

    assert summary["Keep"] == 30
    assert summary["Review"] == 0
    assert summary["Reject"] == 0


def test_negative_close_is_rejected(sample_data):

    sample_data.loc[5, "Close"] = -10.0

    result, _ = apply_cleaning_policy(
        "TEST", sample_data
    )

    assert result.loc[5, "Quality_Status"] == "REJECT"
    assert result.loc[5, "Invalid_Price"]


def test_missing_adjusted_close_is_rejected(sample_data):

    sample_data.loc[5, "Adj Close"] = float("nan")

    result, _ = apply_cleaning_policy(
        "TEST", sample_data
    )

    assert result.loc[5, "Quality_Status"] == "REJECT"
    assert result.loc[5, "Missing_Value"]


def test_invalid_ohlc_is_rejected(sample_data):

    sample_data.loc[5, "High"] = 50.0

    result, _ = apply_cleaning_policy(
        "TEST", sample_data
    )

    assert result.loc[5, "Quality_Status"] == "REJECT"
    assert result.loc[5, "Inconsistent_OHLC"]


def test_negative_volume_is_rejected(sample_data):

    sample_data.loc[5, "Volume"] = -100

    result, _ = apply_cleaning_policy(
        "TEST", sample_data
    )

    assert result.loc[5, "Quality_Status"] == "REJECT"
    assert result.loc[5, "Negative_Volume"]


def test_zero_volume_is_flagged(sample_data):

    sample_data.loc[5, "Volume"] = 0

    result, _ = apply_cleaning_policy(
        "TEST", sample_data
    )

    assert result.loc[5, "Quality_Status"] == "REVIEW"
    assert result.loc[5, "Zero_Volume"]


def test_duplicate_date_is_flagged(sample_data):

    sample_data.loc[5, "Date"] = sample_data.loc[4, "Date"]

    result, _ = apply_cleaning_policy(
        "TEST", sample_data
    )

    assert result.loc[4, "Quality_Status"] == "REVIEW"
    assert result.loc[5, "Quality_Status"] == "REVIEW"


def test_large_return_is_flagged(sample_data):

    # Modify both daily close definitions consistently.
    sample_data.loc[15, "Close"] = 130.0
    sample_data.loc[15, "Adj Close"] = 130.0
    sample_data.loc[15, "High"] = 131.0
    sample_data.loc[15, "Low"] = 100.0

    result, _ = apply_cleaning_policy(
        "TEST", sample_data
    )

    assert result.loc[15, "Quality_Status"] == "REVIEW"
    assert result.loc[15, "Unusual_Return"]


# ---------------------------------------------
# 3. Integration test for actual saved datasets
# ---------------------------------------------

def sha256(path):

    digest = hashlib.sha256()

    with path.open("rb") as file:
        for block in iter(
            lambda: file.read(1024 * 1024), b""
        ):
            digest.update(block)

    return digest.hexdigest()


def test_processed_snapshot_integrity():

    raw_manifest_path = RAW_DIR / "manifest.json"
    processed_manifest_path = (
        PROCESSED_DIR / "processing_manifest.json"
    )

    assert raw_manifest_path.exists()
    assert processed_manifest_path.exists()

    raw_manifest = json.loads(
        raw_manifest_path.read_text(encoding="utf-8")
    )

    processed_manifest = json.loads(
        processed_manifest_path.read_text(
            encoding="utf-8"
        )
    )

    assert processed_manifest["source_snapshot"] == SNAPSHOT_ID

    assert (
        sha256(raw_manifest_path)
        == processed_manifest["source_manifest_hash"]
    )

    raw_records = {
        r["ticker"]: r
        for r in raw_manifest["files"]
    }

    processed_records = {
        r["ticker"]: r
        for r in processed_manifest["files"]
    }

    assert set(raw_records) == set(processed_records)
    assert len(raw_records) == 6

    total_rows = 0
    total_review = 0

    for symbol, raw_record in raw_records.items():

        raw_path = RAW_DIR / raw_record["file"]

        processed_record = processed_records[symbol]

        processed_path = (
            PROCESSED_DIR / processed_record["file"]
        )

        assert sha256(raw_path) == raw_record["sha256"]
        assert (
            sha256(processed_path)
            == processed_record["sha256"]
        )

        raw = pd.read_parquet(raw_path)
        processed = pd.read_parquet(processed_path)

        assert len(raw) == raw_record["rows"]
        assert len(processed) == processed_record["rows"]

        # Compare the original financial columns.
        raw_dates = pd.to_datetime(
            raw["Date"], utc=True
        ).astype("datetime64[ns, UTC]")

        processed_dates = pd.to_datetime(
            processed["Date"], utc=True
        ).astype("datetime64[ns, UTC]")

        assert raw_dates.reset_index(drop=True).equals(
            processed_dates.reset_index(drop=True)
        )

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

        # Independently recalculate the quality labels.
        recalculated, summary = apply_cleaning_policy(
            symbol, raw
        )

        assert (
            recalculated["Quality_Status"].reset_index(
                drop=True
            ).equals(
                processed["Quality_Status"].reset_index(
                    drop=True
                )
            )
        )

        for status in ["KEEP", "REVIEW", "REJECT"]:
            actual = int(
                (processed["Quality_Status"] == status).sum()
            )

            assert actual == processed_record[
                "quality_counts"
            ][status]

        assert summary["Reject"] == 0

        total_rows += len(processed)
        total_review += summary["Review"]

    assert total_rows == 17874
    assert total_review == 35
