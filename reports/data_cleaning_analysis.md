
# Market Data Cleaning and Validation

## Objective

Validate historical market observations, detect
potential anomalies, establish cleaning rules,
and produce reproducible processed datasets.

## Dataset

Source: Yahoo Finance via yfinance

Instruments:
AAPL, MSFT, NVDA, GOOGL, AMZN, SPY

Historical observations: 17,874
Sessions per instrument: 2,979

Source snapshot:
20261107T082129_328387Z

## 1. Exchange Calendar Validation

An independent NYSE trading calendar was used
to validate the dataset.

Results:
- Expected sessions: 2,979 per instrument
- Missing sessions: 0
- Unexpected sessions: 0
- Calendar coverage: 100%

## 2. Return and Anomaly Analysis

Simple daily returns and logarithmic returns
were calculated.

Anomalies were screened using:
- Absolute daily return threshold: 20%
- Modified MAD z-score threshold: 8

Results:
- AAPL: 4 flagged observations
- MSFT: 7
- NVDA: 5
- GOOGL: 3
- AMZN: 6
- SPY: 10

Total flagged observations: 35

These flags do not establish data errors.

## 3. Cleaning Policy

Observations were classified as:

KEEP:
No issues detected by the cleaning rules.

REVIEW:
Unusual returns, duplicate dates, or zero volume.

REJECT:
Missing required values, invalid prices,
negative volume, or inconsistent OHLC.

## 4. Cleaning Results

Total observations: 17,874

KEEP: 17,839
REVIEW: 35
REJECT: 0

All original financial observations were preserved.

No outliers were automatically removed.

## 5. Processed Dataset

Six processed Parquet datasets were produced
from the verified source snapshot.

Processing added quality classifications
and diagnostic flags.

Original prices, dates, and volumes were
verified against the raw observations.

Processed status:
Candidate pending final research validation.

## 6. Automated Testing

Cleaning tests: 9 passed
Full project test suite: 15 passed
Failed tests: 0

Tests included:
- Valid observations
- Negative prices
- Missing values
- Invalid OHLC
- Negative volume
- Zero volume
- Duplicate dates
- Large returns
- Processed dataset integrity

## 7. Limitations

- The data provider has not been independently
  verified for every historical observation.
- Flagged returns are not confirmed data errors.
- Whole-sample MAD statistics are retrospective
  audit tools, not leakage-safe prediction features.
- The stock universe is small and selection-biased.
- Data availability at forecast cutoff remains
  a separate concern for later modelling.
- Test coverage is not exhaustive.

## 8. Conclusion

The implemented dataset checks and cleaning
pipeline passed the automated validation tests.

All 17,874 source observations were retained,
and 35 were marked for further review.

The processed datasets are ready for subsequent
research steps, subject to the documented
limitations and additional validation.
