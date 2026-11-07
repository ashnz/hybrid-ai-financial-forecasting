
# Historical Market Data: Collection and Analysis

## Objective

Collect, validate, preserve, and visualise historical
daily market data for the initial research universe.

## Dataset

Source: Yahoo Finance via yfinance

Instruments:
- AAPL
- MSFT
- NVDA
- GOOGL
- AMZN
- SPY (market benchmark)

Period: 2015-01-02 to 2026-11-05

Frequency: Daily

Total observations: 17,874
Observations per instrument: 2,979

## Data Collection

Historical OHLCV data was retrieved alongside
adjusted closing prices and corporate actions.

The collection uses explicit adjustment settings
and a configuration-driven ticker universe.

## Initial Quality Assessment

Results:
- Missing required values: 0
- Duplicate dates: 0
- Nonpositive prices: 0
- Negative or zero trading volume: 0
- Inconsistent OHLC observations: 0
- Trading-date mismatches relative to SPY: 0

All instruments passed the implemented checks.

These results demonstrate internal consistency,
not independent verification of market prices.

## Data Preservation

Datasets were stored in Parquet format.

Snapshot ID:
20261107T082129_328387Z

Each saved file was reloaded and verified.
SHA-256 hashes were recorded for integrity checking.

Raw datasets are retained locally.

## Visualisation Findings

### Historical Adjusted Prices

The selected instruments experienced substantial
long-term growth, with differing periods of
volatility and price corrections.

### Normalised Price Comparison

NVIDIA exhibited exceptionally large cumulative
adjusted-price growth relative to the others.

A logarithmic axis provided a clearer comparison
of proportional changes.

### Trading Volume

Daily trading volumes showed substantial variation
and occasional spikes.

The usefulness of relative volume as a predictive
feature remains to be tested.

## Limitations

- Data comes from one market-data provider.
- Official exchange-calendar completeness has
  not yet been independently verified.
- Corporate-action adjustments require further study.
- The small stock universe introduces selection bias.
- Historical growth does not establish predictability.
- No predictive model has been trained yet.

## Next Steps

1. Perform more rigorous data validation.
2. Examine suspicious returns and corporate actions.
3. Establish a consistent cleaned dataset.
4. Prepare reproducible feature engineering.
