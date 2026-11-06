
from pathlib import Path
from datetime import date, datetime

import yaml


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "project.yaml"


def load_config():
    with CONFIG_PATH.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def as_date(value):
    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    return date.fromisoformat(str(value))


def test_config_file_exists():
    assert CONFIG_PATH.is_file()


def test_stock_universe():
    config = load_config()
    stocks = config["market"]["stocks"]

    assert len(stocks) == 5
    assert len(stocks) == len(set(stocks))
    assert config["market"]["benchmark"] not in stocks


def test_forecast_horizon():
    config = load_config()

    assert config["forecast"]["horizon_days"] == 5


def test_data_split_order():
    config = load_config()
    splits = config["splits"]

    names = [
        "training",
        "validation",
        "calibration",
        "testing",
        "forward_evaluation",
    ]

    previous_end = None

    for name in names:
        start = as_date(splits[name]["start"])
        end = as_date(splits[name]["end"])

        assert start <= end

        if previous_end is not None:
            assert start > previous_end

        previous_end = end


def test_gap_covers_horizon():
    config = load_config()

    assert (
        config["splits"]["gap_trading_days"]
        >= config["forecast"]["horizon_days"]
    )


def test_research_only_mode():
    config = load_config()

    assert config["execution"]["mode"] == "research_only"
    assert config["execution"]["real_money_trading"] is False
