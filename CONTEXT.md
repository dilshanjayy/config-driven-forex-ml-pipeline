# Config-Driven Forex ML Pipeline

A CLI tool (`fxml`) for config-driven forex model training, designed as a reusable experimentation tool and engineering portfolio piece.

## Language

### Market Data

**OHLCV**:
A single price bar containing open, high, low, close, and volume values for a specific pair, interval, and timestamp.
_Avoid_: candle, candlestick, bar (when referring to the full data record)

**Pair**:
A forex currency pair expressing the exchange rate between two currencies (e.g., EUR/USD).
_Avoid_: symbol, ticker, instrument

**Interval**:
The time period each OHLCV bar represents (e.g., 1h, 1day).
_Avoid_: timeframe, resolution, period (reserve "period" for indicator parameters)

**Pip**:
The smallest standard unit of price movement for a pair. 0.0001 for most pairs, 0.01 for JPY pairs.
_Avoid_: point, tick

### Pipeline Concepts

**Feature**:
A computed column derived from OHLCV data via a registered feature function (e.g., RSI, EMA). Features are backward-looking.
_Avoid_: indicator (when referring to the pipeline concept; "indicator" is acceptable when discussing the underlying technical analysis concept)

**Label**:
The target variable for model training, computed from future price movement via a registered labeling strategy. Labels are forward-looking.
_Avoid_: target, signal, class (when referring to the computation; "class" is acceptable when referring to the output categories buy/sell/hold)

**Warm-up Period**:
The initial rows of data where lagged features produce NaN values due to insufficient lookback history. Always trimmed automatically before training.
_Avoid_: burn-in, ramp-up

**Embargo**:
The number of bars removed between train and validation/test sets to prevent label lookahead leakage. Auto-derived from the labeling strategy's lookahead_bars.
_Avoid_: gap, buffer, guard band

**Run**:
A single execution of the training pipeline, producing a self-contained directory with the config, trained model, fitted scaler, and metrics.
_Avoid_: experiment (reserve for MLflow's concept), job, execution

### Registry

**Registry**:
A name-to-function mapping that allows config-driven lookup of features, labels, and models by string name.
_Avoid_: plugin system, factory

### Splits

**Split Date**:
The boundary between the train and validation (or test) sets. Everything before it is train, everything on or after is validation/test.
_Avoid_: cutoff, boundary

**Validation Set**:
An optional held-out portion of data used for hyperparameter tuning and model comparison. Metrics are shown by default.
_Avoid_: dev set

**Test Set**:
A held-out portion of data used for final model evaluation only. Metrics are hidden by default when a validation set is present to prevent leakage through human decision-making.
_Avoid_: holdout
