
# Historical Financial Market Visualisation

from pathlib import Path
import hashlib
import json

import matplotlib.pyplot as plt
import pandas as pd
import yaml


# ----------------------------------------
# 1. Project configuration
# ----------------------------------------

ROOT = Path(__file__).resolve().parents[1]

with (ROOT / "config" / "project.yaml").open(
    "r", encoding="utf-8"
) as file:
    config = yaml.safe_load(file)

STOCKS = config["market"]["stocks"]
BENCHMARK = config["market"]["benchmark"]

TICKERS = list(dict.fromkeys(
    STOCKS + [BENCHMARK]
))

# Use the verified snapshot from Step 2.3.
SNAPSHOT_ID = "20261107T082129_328387Z"

SNAPSHOT_DIR = ROOT / "data" / "raw" / SNAPSHOT_ID

FIGURE_DIR = ROOT / "reports" / "figures"
FIGURE_DIR.mkdir(parents=True, exist_ok=True)


# ----------------------------------------
# 2. Verify and load saved data
# ----------------------------------------

def file_sha256(path):
    digest = hashlib.sha256()

    with path.open("rb") as file:
        for block in iter(
            lambda: file.read(1024 * 1024), b""
        ):
            digest.update(block)

    return digest.hexdigest()


def load_datasets():

    manifest_path = SNAPSHOT_DIR / "manifest.json"

    if not manifest_path.exists():
        raise FileNotFoundError(
            f"Missing manifest: {manifest_path}"
        )

    with manifest_path.open(
        "r", encoding="utf-8"
    ) as file:
        manifest = json.load(file)

    if manifest["snapshot_id"] != SNAPSHOT_ID:
        raise ValueError("Snapshot ID does not match manifest")

    records = {
        record["ticker"]: record
        for record in manifest["files"]
    }

    datasets = {}

    for symbol in TICKERS:

        if symbol not in records:
            raise ValueError(
                f"{symbol} missing from manifest"
            )

        record = records[symbol]
        file_path = SNAPSHOT_DIR / record["file"]

        if not file_path.exists():
            raise FileNotFoundError(file_path)

        if file_sha256(file_path) != record["sha256"]:
            raise ValueError(
                f"{symbol}: File integrity check failed"
            )

        df = pd.read_parquet(file_path)

        required = [
            "Date",
            "Adj Close",
            "Volume"
        ]

        missing = [
            col for col in required
            if col not in df.columns
        ]

        if missing:
            raise ValueError(
                f"{symbol}: Missing columns {missing}"
            )

        if len(df) != record["rows"]:
            raise ValueError(
                f"{symbol}: Unexpected row count"
            )

        df["Date"] = pd.to_datetime(df["Date"])

        df = df.sort_values("Date").reset_index(
            drop=True
        )

        datasets[symbol] = df

        print(
            f"{symbol}: {len(df)} observations "
            f"loaded and verified"
        )

    return datasets


# ----------------------------------------
# 3. Historical adjusted prices
# ----------------------------------------

def plot_historical_prices(datasets):

    fig, axes = plt.subplots(
        3, 2,
        figsize=(14, 11),
        sharex=True
    )

    for ax, symbol in zip(axes.flat, TICKERS):

        df = datasets[symbol]

        ax.plot(
            df["Date"],
            df["Adj Close"],
            linewidth=1.2
        )

        ax.set_title(symbol)
        ax.set_ylabel("Adjusted close (USD)")
        ax.grid(alpha=0.25)

    fig.suptitle(
        "Historical Adjusted Closing Prices",
        fontsize=16
    )

    fig.tight_layout()

    output = (
        FIGURE_DIR / "historical_prices.png"
    )

    fig.savefig(
        output,
        dpi=200,
        bbox_inches="tight"
    )

    plt.close(fig)
    print("Saved:", output)


# ----------------------------------------
# 4. Normalised performance comparison
# ----------------------------------------

def plot_normalised_prices(datasets):

    fig, ax = plt.subplots(figsize=(14, 7))

    for symbol in TICKERS:

        df = datasets[symbol]

        prices = df["Adj Close"]

        if prices.isna().any() or (prices <= 0).any():
            raise ValueError(
                f"{symbol}: Invalid prices for normalisation"
            )

        first_price = prices.iloc[0]

        normalised = (
            prices / first_price
        ) * 100

        ax.plot(
            df["Date"],
            normalised,
            label=symbol,
            linewidth=1.3
        )

        print(
            f"{symbol}: Final index = "
            f"{normalised.iloc[-1]:.2f}"
        )
    ax.set_yscale("log")

    ax.set_title(
        "Normalised Adjusted Price(Logarithmic Scale)"
    )

    ax.set_xlabel("Date")
    ax.set_ylabel("Indexed value (Start = 100)")
    ax.legend()
    ax.grid(alpha=0.25)

    fig.tight_layout()

    output = (
        FIGURE_DIR / "normalised_prices_log.png"
    )

    fig.savefig(
        output,
        dpi=200,
        bbox_inches="tight"
    )
    

    plt.close(fig)
    print("Saved:", output)


# ----------------------------------------
# 5. Historical trading volume
# ----------------------------------------

def plot_trading_volume(datasets):

    fig, axes = plt.subplots(
        3, 2,
        figsize=(14, 11),
        sharex=True
    )

    for ax, symbol in zip(axes.flat, TICKERS):

        df = datasets[symbol]

        ax.plot(
            df["Date"],
            df["Volume"] / 1_000_000,
            linewidth=0.8
        )

        ax.set_title(symbol)
        ax.set_ylabel("Volume (millions)")
        ax.grid(alpha=0.25)

    fig.suptitle(
        "Historical Daily Trading Volume",
        fontsize=16
    )

    fig.tight_layout()

    output = (
        FIGURE_DIR / "trading_volume.png"
    )

    fig.savefig(
        output,
        dpi=200,
        bbox_inches="tight"
    )

    plt.close(fig)
    print("Saved:", output)


# ----------------------------------------
# 6. Main execution
# ----------------------------------------

def main():

    print("=" * 60)
    print("FINANCIAL MARKET VISUALISATION")
    print("=" * 60)

    print("\nLoading snapshot:", SNAPSHOT_ID)

    datasets = load_datasets()

    print("\nGenerating historical price plots...")
    plot_historical_prices(datasets)

    print("\nGenerating normalised comparison...")
    plot_normalised_prices(datasets)

    print("\nGenerating volume plots...")
    plot_trading_volume(datasets)

    print("\nVISUALISATION: PASS")
    print("Graphs saved to:", FIGURE_DIR)


if __name__ == "__main__":
    main()
