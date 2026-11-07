
from src.data_storage import save_market_datasets
from src.data_quality import (
    inspect_dataset,
    compare_trading_dates
)

from pathlib import Path
from datetime import date, timedelta

import pandas as pd
import yfinance as yf
import yaml


# Project location
ROOT = Path(__file__).resolve().parents[1]

# Load project configuration
CONFIG_PATH = ROOT / "config" / "project.yaml"

with CONFIG_PATH.open("r", encoding="utf-8") as file:
    config = yaml.safe_load(file)


# Financial instruments
stocks = config["market"]["stocks"]
benchmark = config["market"]["benchmark"]

tickers = list(dict.fromkeys(stocks + [benchmark]))


# Historical period
start_date = str(config["data"]["start_date"])

last_date = date.fromisoformat(
    str(config["data"]["end_date"])
)

end_date = (
    last_date + timedelta(days=1)
).isoformat()


# Download function
def download_market_data(symbol):

    print(f"\nDownloading {symbol}...")

    stock = yf.Ticker(symbol)

    data = stock.history(
        start=start_date,
        end=end_date,
        interval="1d",
        auto_adjust=False,
        actions=True,
        repair=False,
        keepna=True,
        timeout=30
    )

    if data.empty:
        raise ValueError(
            f"No historical data returned for {symbol}"
        )

    data = data.reset_index()

    data.insert(0, "Ticker", symbol)

    return data


# Main program
def main():

    print("=" * 55)
    print("HISTORICAL MARKET DATA COLLECTION")
    print("=" * 55)

    datasets = {}
    failures = {}

    for symbol in tickers:

        try:
            data = download_market_data(symbol)

            datasets[symbol] = data
            inspect_dataset(symbol, data)

            print(f"Rows: {len(data)}")
            print(f"Columns: {len(data.columns)}")

            print("\nFirst observation:")
            print(data.head(1).to_string(index=False))

            print("\nLast observation:")
            print(data.tail(1).to_string(index=False))

        except Exception as error:
            failures[symbol] = str(error)
            print(f"Failed: {symbol} - {error}")

    if len(datasets) == len(tickers):
        compare_trading_dates(datasets)

    print("\n" + "=" * 55)
    print("COLLECTION SUMMARY")
    print("=" * 55)

    for symbol, data in datasets.items():
        print(
            f"{symbol}: {len(data)} observations"
        )

    print(
        f"\nSuccessful downloads: "
        f"{len(datasets)}/{len(tickers)}"
    )

    if failures:
        print("\nFailed downloads:")

        for symbol, error in failures.items():
            print(f"{symbol}: {error}")

        return 1

    # Preserve the collected datasets.
    try:
        snapshot_dir = save_market_datasets(
            datasets,
            config
        )

    except Exception as error:
        print(
            "\nDATA STORAGE FAILED: "
            f"{type(error).__name__}: {error}"
        )
        return 1

    print("\nMARKET DATA COLLECTION: PASS")
    print(f"Verified snapshot: {snapshot_dir}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
