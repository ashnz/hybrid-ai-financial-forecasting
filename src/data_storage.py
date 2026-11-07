
# Raw Financial Data Storage and Verification

from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

import pandas as pd
import yfinance as yf
from pandas.testing import assert_frame_equal


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"


def calculate_sha256(file_path):
    """Calculate a SHA-256 fingerprint of a file."""

    digest = hashlib.sha256()

    with open(file_path, "rb") as file:
        for block in iter(
            lambda: file.read(1024 * 1024), b""
        ):
            digest.update(block)

    return digest.hexdigest()


def verify_saved_data(original, restored, symbol):
    """Verify the saved data matches the source DataFrame."""

    # Verify structure
    assert original.columns.tolist() == restored.columns.tolist(), (
        f"{symbol}: Column names or order changed"
    )

    assert len(original) == len(restored), (
        f"{symbol}: Row count changed"
    )

    # Normalise datetime precision before comparison
    original_dates = pd.to_datetime(
        original["Date"], utc=True
    ).astype("datetime64[ns, UTC]")

    restored_dates = pd.to_datetime(
        restored["Date"], utc=True
    ).astype("datetime64[ns, UTC]")

    assert original_dates.reset_index(drop=True).equals(
        restored_dates.reset_index(drop=True)
    ), f"{symbol}: Date values changed"

    # Verify all financial columns exactly
    original_values = (
        original.drop(columns=["Date"])
        .reset_index(drop=True)
    )

    restored_values = (
        restored.drop(columns=["Date"])
        .reset_index(drop=True)
    )

    assert_frame_equal(
        original_values,
        restored_values,
        check_dtype=True,
        check_exact=True
    )


def save_market_datasets(datasets, config):
    """Save and verify a dated market-data snapshot."""

    RAW_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc)

    snapshot_id = timestamp.strftime(
        "%Y%m%dT%H%M%S_%fZ"
    )

    snapshot_dir = RAW_DIR / snapshot_id
    snapshot_dir.mkdir(exist_ok=False)

    manifest = {
        "snapshot_id": snapshot_id,
        "downloaded_at_utc": timestamp.isoformat(),
        "source": "Yahoo Finance via yfinance",
        "yfinance_version": yf.__version__,
        "start_date": str(config["data"]["start_date"]),
        "end_date_inclusive": str(config["data"]["end_date"]),
        "interval": "1d",
        "auto_adjust": False,
        "actions": True,
        "repair": False,
        "keepna": True,
        "files": []
    }

    print("\n" + "=" * 55)
    print("RAW DATA STORAGE")
    print("=" * 55)

    for symbol, df in datasets.items():

        file_name = f"{symbol}_daily.parquet"
        file_path = snapshot_dir / file_name

        # Preserve the downloaded observations
        df_to_save = df.copy()

        # Save as Parquet
        df_to_save.to_parquet(
            file_path,
            engine="pyarrow",
            index=False
        )

        # Reload the saved data
        restored = pd.read_parquet(
            file_path,
            engine="pyarrow"
        )

        # Verify that the information was preserved
        verify_saved_data(
            df_to_save,
            restored,
            symbol
        )

        # Calculate file-integrity hash
        file_hash = calculate_sha256(file_path)

        record = {
            "ticker": symbol,
            "file": file_name,
            "rows": len(df_to_save),
            "columns": len(df_to_save.columns),
            "first_date": str(df_to_save["Date"].iloc[0]),
            "last_date": str(df_to_save["Date"].iloc[-1]),
            "sha256": file_hash
        }

        manifest["files"].append(record)

        print(f"\n{symbol}: SAVED AND VERIFIED")
        print(f"Rows: {len(df_to_save)}")
        print(f"File: {file_name}")
        print(f"SHA-256: {file_hash[:16]}...")

    manifest_path = snapshot_dir / "manifest.json"

    manifest_path.write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8"
    )

    print("\n" + "=" * 55)
    print("STORAGE SUMMARY")
    print("=" * 55)

    print(f"Snapshot: {snapshot_id}")
    print(f"Datasets saved: {len(datasets)}")
    print(f"Location: {snapshot_dir}")
    print("Verification: PASS")

    return snapshot_dir
