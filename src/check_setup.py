
from pathlib import Path
from datetime import date, datetime
from importlib.metadata import version, PackageNotFoundError
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import sys

import yaml


# -----------------------------------------
# 1. Locate the project
# -----------------------------------------

ROOT = Path(__file__).resolve().parents[1]

CONFIG_FILE = ROOT / "config" / "project.yaml"

REQUIRED_FOLDERS = [
    "config",
    "docs",
    "src",
    "tests",
    "data/raw",
    "data/processed",
    "notebooks",
    "models",
    "reports",
    "reports/figures",
]

REQUIRED_PACKAGES = [
    "numpy",
    "pandas",
    "pyarrow",
    "duckdb",
    "yfinance",
    "matplotlib",
    "plotly",
    "scikit-learn",
    "xgboost",
    "PyYAML",
    "pytest",
    "tzdata",
    "streamlit",
]


# -----------------------------------------
# 2. Helper functions
# -----------------------------------------

def check_folders():
    print("\n[1] Checking folder structure")

    missing = []

    for folder in REQUIRED_FOLDERS:
        path = ROOT / folder

        if path.is_dir():
            print(f"  PASS  {folder}")
        else:
            print(f"  FAIL  {folder}")
            missing.append(folder)

    return not missing


def check_packages():
    print("\n[2] Checking Python libraries")

    missing = []

    for package in REQUIRED_PACKAGES:
        try:
            installed_version = version(package)
            print(f"  PASS  {package}: {installed_version}")

        except PackageNotFoundError:
            print(f"  FAIL  {package}: not installed")
            missing.append(package)

    return not missing


def load_config():
    print("\n[3] Loading configuration")

    if not CONFIG_FILE.is_file():
        raise FileNotFoundError(
            f"Configuration not found: {CONFIG_FILE}"
        )

    with CONFIG_FILE.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    if not isinstance(config, dict):
        raise ValueError("Configuration must be a YAML mapping.")

    print("  PASS  YAML configuration loaded")

    return config


def parse_date(value):
    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    return date.fromisoformat(str(value))


def validate_config(config):
    print("\n[4] Validating project settings")

    errors = []

    def require(condition, message):
        if condition:
            print(f"  PASS  {message}")
        else:
            print(f"  FAIL  {message}")
            errors.append(message)

    project = config["project"]
    market = config["market"]
    forecast = config["forecast"]
    data = config["data"]
    splits = config["splits"]
    execution = config["execution"]

    require(
        isinstance(project["random_seed"], int),
        "Random seed is an integer"
    )

    stocks = market["stocks"]

    require(
        isinstance(stocks, list)
        and len(stocks) > 0
        and len(stocks) == len(set(stocks)),
        "Stock symbols are nonempty and unique"
    )

    require(
        market["benchmark"] not in stocks,
        "Benchmark is separate from stock universe"
    )

    require(
        market["frequency"] == "1d",
        "Daily data frequency selected"
    )

    horizon = forecast["horizon_days"]

    require(
        isinstance(horizon, int) and horizon > 0,
        "Forecast horizon is a positive integer"
    )

    require(
        execution["mode"] == "research_only"
        and execution["real_money_trading"] is False,
        "Research-only execution mode enabled"
    )

    try:
        ZoneInfo(forecast["timezone"])
        datetime.strptime(forecast["cutoff_time"], "%H:%M")
        print("  PASS  Forecast timezone and cutoff are valid")
    except (ValueError, ZoneInfoNotFoundError) as exc:
        print(f"  FAIL  Invalid forecast time setting: {exc}")
        errors.append("Invalid forecast time setting")

    ranges = [
        "training",
        "validation",
        "calibration",
        "testing",
        "forward_evaluation",
    ]

    previous_end = None

    for name in ranges:
        start = parse_date(splits[name]["start"])
        end = parse_date(splits[name]["end"])

        require(
            start <= end,
            f"{name}: start date is not after end date"
        )

        if previous_end is not None:
            require(
                start > previous_end,
                f"{name}: follows the previous date range"
            )

        previous_end = end

    data_start = parse_date(data["start_date"])
    data_end = parse_date(data["end_date"])

    first_start = parse_date(splits["training"]["start"])
    last_end = parse_date(
        splits["forward_evaluation"]["end"]
    )

    require(
        data_start <= first_start and data_end >= last_end,
        "Data coverage contains all evaluation periods"
    )

    require(
        splits["gap_trading_days"] >= horizon,
        "Boundary gap covers the forecast horizon"
    )

    print("\n[5] Project summary")
    print(f"  Name: {project['name']}")
    print(f"  Version: {project['version']}")
    print(f"  Stocks: {', '.join(stocks)}")
    print(f"  Benchmark: {market['benchmark']}")
    print(f"  Forecast horizon: {horizon} trading days")
    print(
        f"  Forecast cutoff: {forecast['cutoff_time']} "
        f"{forecast['timezone']}"
    )

    return not errors


# -----------------------------------------
# 3. Execute setup checks
# -----------------------------------------

def main():
    print("=" * 58)
    print("HYBRID AI FINANCIAL FORECASTING")
    print("STAGE 1 - ENVIRONMENT VERIFICATION")
    print("=" * 58)

    print(f"\nPython version: {sys.version.split()[0]}")
    print(f"Project root: {ROOT}")

    folders_ok = check_folders()
    packages_ok = check_packages()

    try:
        config = load_config()
        config_ok = validate_config(config)

    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"\nCONFIGURATION ERROR: {exc}")
        config_ok = False

    success = folders_ok and packages_ok and config_ok

    print("\n" + "=" * 58)

    if success:
        print("STAGE 1 SETUP: PASS")
    else:
        print("STAGE 1 SETUP: FAIL")

    print("=" * 58)

    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
