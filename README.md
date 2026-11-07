<<<<<<< HEAD

# Hybrid AI Financial Forecasting System

A research project developing a hybrid machine-learning
system that combines historical stock market data,
financial news sentiment, and time-series features
to produce probabilistic financial forecasts.

## Objectives

1. Collect and preprocess historical financial data.
2. Engineer market and volatility features.
3. Train and compare price-prediction models.
4. Analyse financial news using NLP.
5. Develop a hybrid price-and-news forecasting model.
6. Evaluate results using chronological backtesting.
7. Build an interactive research dashboard.

## Initial Scope

- Market: US equities
- Stocks: AAPL, MSFT, NVDA, GOOGL, AMZN
- Benchmark: SPY
- Prediction horizon: 5 trading sessions
- Primary evaluation metric: Brier score

## Technology

Python, Pandas, NumPy, scikit-learn,
XGBoost, DuckDB, FinBERT (planned),
Matplotlib, Plotly, and Streamlit.

## Development Progress

- [x] Stage 1: Project Setup and Research Protocol
- [x] Stage 2: Market Data Collection
- [x] Stage 3: Data Cleaning and Validation
- [ ] Stage 4: Exploratory Data Analysis
- [ ] Stage 5: Feature Engineering
- [ ] Stage 6: Chronological Splitting
- [ ] Stage 7: Baseline Model Training
- [ ] Stage 8: Hyperparameter Tuning and Selection
- [ ] Stage 9: Financial News Intelligence
- [ ] Stage 10: Hybrid AI Integration
- [ ] Stage 11: Model Evaluation and Backtesting
- [ ] Stage 12: Interactive Dashboard
- [ ] Stage 13: Monitoring and Improvements

## Research Methodology

See docs/EXPERIMENT_PROTOCOL.md.

## Historical Market Data Analysis

Historical daily prices were collected for five US
stocks and the SPY benchmark.

All 17,874 observations passed the initial
internal data-quality checks.

The datasets were preserved in Parquet format,
with timestamped snapshots and integrity hashes.

See [Market Data Analysis](reports/market_data_analysis.md)
for findings, limitations, and visualisations.

## Data Cleaning and Validation

The historical dataset contains 17,874 observations
across five US stocks and the SPY benchmark.

Results:
- NYSE calendar coverage: 100%
- Missing trading sessions: 0
- Observations flagged for review: 35
- Rejected observations: 0
- Automated project tests passed: 15/15

Raw observations are preserved, with processed
datasets stored separately.

See [Data Cleaning Analysis](reports/data_cleaning_analysis.md).


## Disclaimer

This is an experimental machine-learning research
project. Its forecasts are not guaranteed and
should not be interpreted as investment advice.
=======

