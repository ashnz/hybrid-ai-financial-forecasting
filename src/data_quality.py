
import pandas as pd


REQUIRED_COLUMNS = [
    "Date",
    "Open",
    "High",
    "Low",
    "Close",
    "Adj Close",
    "Volume",
]


def inspect_dataset(symbol, df):
    """Inspect a raw market dataset without changing it."""

    print(f"\n{'=' * 55}")
    print(f"DATA QUALITY: {symbol}")
    print(f"{'=' * 55}")

    missing_columns = [
        col for col in REQUIRED_COLUMNS
        if col not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"{symbol}: Missing columns {missing_columns}"
        )

    # Missing values by column
    missing = df[REQUIRED_COLUMNS].isna().sum()

    print("\nMissing values:")
    print(missing.to_string())

    # Date uniqueness
    duplicate_dates = int(
        df["Date"].duplicated().sum()
    )

    # Numeric validity
    prices = df[
        ["Open", "High", "Low", "Close", "Adj Close"]
    ]

    invalid_prices = (
        prices.le(0) & prices.notna()
    ).any(axis=1)

    negative_volume = (
        df["Volume"].lt(0) & df["Volume"].notna()
    )

    zero_volume = df["Volume"].eq(0)

    # Check whether OHLC values agree logically.
    valid_ohlc = df[
        ["Open", "High", "Low", "Close"]
    ].notna().all(axis=1)

    inconsistent_ohlc = valid_ohlc & (
        (df["High"] < df["Low"])
        | (df["Open"] > df["High"])
        | (df["Open"] < df["Low"])
        | (df["Close"] > df["High"])
        | (df["Close"] < df["Low"])
    )

    # Check chronological ordering.
    dates = pd.to_datetime(df["Date"])

    chronological = dates.is_monotonic_increasing

    # Corporate-action counts.
    dividend_events = (
        int(df["Dividends"].fillna(0).ne(0).sum())
        if "Dividends" in df.columns else None
    )

    split_events = (
        int(df["Stock Splits"].fillna(0).ne(0).sum())
        if "Stock Splits" in df.columns else None
    )

    summary = {
        "Ticker": symbol,
        "Rows": len(df),
        "Missing_Cells": int(missing.sum()),
        "Duplicate_Dates": duplicate_dates,
        "Invalid_Price_Rows": int(invalid_prices.sum()),
        "Negative_Volume_Rows": int(negative_volume.sum()),
        "Zero_Volume_Rows": int(zero_volume.sum()),
        "Inconsistent_OHLC_Rows": int(
            inconsistent_ohlc.sum()
        ),
        "Chronological": chronological,
        "Dividend_Events": dividend_events,
        "Split_Events": split_events,
    }

    print("\nQuality summary:")

    for key, value in summary.items():
        print(f"{key}: {value}")

    return summary


def compare_trading_dates(datasets):
    """Compare available trading dates against SPY."""

    print(f"\n{'=' * 55}")
    print("CROSS-STOCK TRADING DATE ALIGNMENT")
    print(f"{'=' * 55}")

    benchmark_dates = set(
        pd.to_datetime(
            datasets["SPY"]["Date"]
        ).dt.date
    )

    for symbol, df in datasets.items():
        stock_dates = set(
            pd.to_datetime(df["Date"]).dt.date
        )

        missing_vs_spy = benchmark_dates - stock_dates
        extra_vs_spy = stock_dates - benchmark_dates

        print(
            f"{symbol}: "
            f"Missing vs SPY = {len(missing_vs_spy)}, "
            f"Extra vs SPY = {len(extra_vs_spy)}"
        )
