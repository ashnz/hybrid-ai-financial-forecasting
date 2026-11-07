
# Exchange Calendar Validation
# Hybrid AI Financial Forecasting System

from pathlib import Path
import json

import pandas as pd
import pandas_market_calendars as mcal
import yaml


ROOT = Path(__file__).resolve().parents[1]

RAW_DIR = ROOT / "data" / "raw"
REPORT_DIR = ROOT / "reports"

SNAPSHOT_ID = "20261107T082129_328387Z"
SNAPSHOT_DIR = RAW_DIR / SNAPSHOT_ID

REPORT_DIR.mkdir(parents=True, exist_ok=True)


# ----------------------------------------
# 1. Load configuration and manifest
# ----------------------------------------

def load_settings():

    with (
        ROOT / "config" / "project.yaml"
    ).open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    with (
        SNAPSHOT_DIR / "manifest.json"
    ).open("r", encoding="utf-8") as file:
        manifest = json.load(file)

    if manifest["snapshot_id"] != SNAPSHOT_ID:
        raise ValueError("Snapshot ID mismatch")

    return config, manifest


# ----------------------------------------
# 2. Generate expected market sessions
# ----------------------------------------

def get_exchange_sessions(start_date, end_date):

    exchange = mcal.get_calendar("NYSE")

    schedule = exchange.schedule(
        start_date=start_date,
        end_date=end_date
    )

    expected_dates = set(
        schedule.index.date
    )

    print("\nNYSE EXPECTED TRADING SESSIONS")
    print("First session:", min(expected_dates))
    print("Last session:", max(expected_dates))
    print("Total sessions:", len(expected_dates))

    return expected_dates


# ----------------------------------------
# 3. Compare individual datasets
# ----------------------------------------

def validate_ticker(symbol, expected_dates):

    file_path = (
        SNAPSHOT_DIR / f"{symbol}_daily.parquet"
    )

    df = pd.read_parquet(file_path)

    dates = pd.to_datetime(df["Date"])

    # Extract the local trading-session date.
    actual_dates = set(dates.dt.date)

    missing_dates = sorted(
        expected_dates - actual_dates
    )

    unexpected_dates = sorted(
        actual_dates - expected_dates
    )

    report = {
        "Ticker": symbol,
        "Expected_Sessions": len(expected_dates),
        "Actual_Sessions": len(actual_dates),
        "Missing_Sessions": len(missing_dates),
        "Unexpected_Sessions": len(unexpected_dates),
        "Coverage_Percent": round(
            100 * len(
                expected_dates & actual_dates
            ) / len(expected_dates),
            4
        ),
    }

    exceptions = []

    for day in missing_dates:
        exceptions.append({
            "Ticker": symbol,
            "Date": str(day),
            "Issue": "Missing expected session"
        })

    for day in unexpected_dates:
        exceptions.append({
            "Ticker": symbol,
            "Date": str(day),
            "Issue": "Unexpected session"
        })

    print(f"\n{symbol}")
    print("Expected:", len(expected_dates))
    print("Actual unique dates:", len(actual_dates))
    print("Missing sessions:", len(missing_dates))
    print("Unexpected sessions:", len(unexpected_dates))
    print("Coverage:", report["Coverage_Percent"], "%")

    if missing_dates:
        print(
            "First missing dates:",
            missing_dates[:10]
        )

    if unexpected_dates:
        print(
            "Unexpected dates:",
            unexpected_dates[:10]
        )

    return report, exceptions


# ----------------------------------------
# 4. Execute calendar validation
# ----------------------------------------

def main():

    print("=" * 60)
    print("EXCHANGE CALENDAR VALIDATION")
    print("=" * 60)

    config, manifest = load_settings()

    start_date = config["data"]["start_date"]
    end_date = config["data"]["end_date"]

    tickers = (
        config["market"]["stocks"]
        + [config["market"]["benchmark"]]
    )

    manifest_tickers = {
        record["ticker"]
        for record in manifest["files"]
    }

    if set(tickers) != manifest_tickers:
        raise ValueError(
            "Configured instruments do not match snapshot"
        )

    expected_dates = get_exchange_sessions(
        start_date,
        end_date
    )

    reports = []
    all_exceptions = []

    for symbol in tickers:

        report, exceptions = validate_ticker(
            symbol,
            expected_dates
        )

        reports.append(report)
        all_exceptions.extend(exceptions)

    # Export audit findings only.
    summary_df = pd.DataFrame(reports)

    exceptions_df = pd.DataFrame(
        all_exceptions,
        columns=["Ticker", "Date", "Issue"]
    )

    summary_df.to_csv(
        REPORT_DIR / "calendar_validation.csv",
        index=False
    )

    exceptions_df.to_csv(
        REPORT_DIR / "calendar_exceptions.csv",
        index=False
    )

    print("\n" + "=" * 60)
    print("CALENDAR VALIDATION SUMMARY")
    print("=" * 60)

    print(summary_df.to_string(index=False))

    print(
        "\nTotal flagged date exceptions:",
        len(exceptions_df)
    )

    if exceptions_df.empty:
        print("CALENDAR VALIDATION: PASS")
    else:
        print("CALENDAR VALIDATION: REVIEW REQUIRED")


if __name__ == "__main__":
    main()
