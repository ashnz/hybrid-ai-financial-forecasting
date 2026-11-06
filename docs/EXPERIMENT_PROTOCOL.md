
# Experiment Protocol

## 1. Research Objective

Develop and evaluate a hybrid AI forecasting system
combining historical equity market data and
financial news sentiment.

Primary research question:

Does adding financial news improve out-of-sample
stock return predictions compared with price-only
machine learning models?

## 2. Initial Market

Market: US equities

Stocks:
- AAPL
- MSFT
- NVDA
- GOOGL
- AMZN

Benchmark: SPY

Initial historical range: 2015-2026

## 3. Prediction Target

Primary horizon: 5 trading sessions

Primary target:

y(t) = 1 if P(t+5) > P(t), otherwise 0

P represents a consistently adjusted closing price.

The model predicts the probability of a positive
five-session forward return.

## 4. Information Availability

Daily prediction cutoff:
20:00 America/New_York

All model input features must be available by
the specified prediction cutoff.

We must account for:
- Market trading sessions
- News publication timestamps
- Economic data release times
- Revisions to historical datasets
- Corporate actions and adjusted prices

## 5. Dataset Splitting

Initial price-model partitions:

Training: 2015-2021
Validation: 2022
Calibration: 2023
Final test: 2024-2025
Additional evaluation: 2026 onward

Apply appropriate boundary gaps to avoid
overlapping prediction-label leakage.

The final test data must not influence feature
selection, hyperparameter selection, or calibration.

Hybrid-model partitions will be determined after
verifying historical news availability.

## 6. Models

Initial baselines:
- Constant probability
- Historical momentum heuristic
- Logistic Regression

Main price model:
- XGBoost

News processing:
- FinBERT sentiment features
- Company and event matching

Hybrid model:
- Combined market and news features with XGBoost

Other models may be added after baseline evaluation.

## 7. Evaluation Metrics

Primary:
- Brier score

Secondary:
- Log loss
- Balanced accuracy
- ROC AUC
- Probability calibration

Additional:
- Forecast stability
- Performance by stock
- Performance by market regime

Simulated portfolio analysis, if introduced,
will report fees, slippage, drawdown, and
appropriate benchmarks.

## 8. Leakage Prevention

Never use future information in training features.

Fit scalers, imputers, and other learned
preprocessing only on the training partition.

Use chronological evaluation.

Avoid overlap between training labels and
subsequent evaluation periods.

Record the original availability time of
news and economic features.

## 9. Research Integrity

Report both successful and unsuccessful experiments.

Record:
- Dataset version
- Feature set
- Model configuration
- Random seed
- Training dates
- Evaluation dates
- Metrics
- Limitations

Do not describe in-sample performance as
independent predictive performance.

## 10. Execution Scope

The initial project is for research,
forecast evaluation, and paper simulation.

No broker integration or live order execution
is included in the research prototype.
