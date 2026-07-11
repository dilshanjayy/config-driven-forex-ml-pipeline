# Config-Driven Forex ML Pipeline — Design Plan

## Overview

A CLI tool (`forex-pipeline`) that enables config-driven forex model training. All training parameters — data source, features, labels, splits, model hyperparameters, preprocessing — are specified in a YAML config file and validated via Pydantic v2.

---

## Architecture Decisions

| Decision | Choice |
|---|---|
| Language | Python |
| Config format | YAML |
| Config validation | Pydantic v2 |
| CLI framework | Typer + Rich |
| Data storage | PostgreSQL (single `ohlcv` table) |
| Data ingestion | TwelveData API → Postgres (separate `data sync` command) |
| Feature engineering | Registry pattern (named feature functions) |
| Labeling | Registry pattern (named labeling strategies) |
| Models | Pluggable registry — scikit-learn first, PyTorch later |
| Prediction task | Classification (buy / sell / hold) |
| Train/test split | Chronological split (walk-forward and purged k-fold later) |
| Preprocessing | Feature scaling + missing data handling |
| Experiment tracking | MLflow |
| Packaging | Poetry + pyproject.toml |
| Testing | pytest + pytest-cov |
| CI | GitHub Actions |
| Terminal output | Rich (progress bars, tables, colored logs) |
| DB connection | `DATABASE_URL` environment variable (python-dotenv) |

---

## CLI Commands (v1)

```
forex-pipeline data sync --pair EUR/USD --interval 1h [--start 2020-01-01] [--end 2024-12-31]
forex-pipeline train --config config.yaml [--run-name my_experiment]
```

### `data sync`
- Fetches OHLCV data from TwelveData API
- Upserts into the `ohlcv` Postgres table
- Shows progress via Rich progress bar
- Supports multiple pairs and intervals

### `train`
- Loads and validates YAML config via Pydantic
- Reads data from Postgres for the specified pair/interval/date range
- Generates features via the feature registry
- Generates labels via the label registry
- Applies preprocessing (scaling, missing data handling)
- Splits data chronologically
- Trains the specified model
- Logs params, metrics, artifacts, and model to MLflow
- Outputs metrics summary to terminal via Rich table

---

## Database Schema

```sql
CREATE TABLE ohlcv (
    id          BIGSERIAL PRIMARY KEY,
    pair        VARCHAR(10) NOT NULL,     -- e.g. 'EUR/USD'
    interval    VARCHAR(5)  NOT NULL,     -- e.g. '1h', '15m', '1d'
    timestamp   TIMESTAMPTZ NOT NULL,
    open        DOUBLE PRECISION NOT NULL,
    high        DOUBLE PRECISION NOT NULL,
    low         DOUBLE PRECISION NOT NULL,
    close       DOUBLE PRECISION NOT NULL,
    volume      DOUBLE PRECISION DEFAULT 0,

    UNIQUE(pair, interval, timestamp)
);

CREATE INDEX idx_ohlcv_pair_interval_ts ON ohlcv(pair, interval, timestamp);
```

---

## Example Config (`config.yaml`)

```yaml
# === Data ===
data:
  pair: "EUR/USD"
  interval: "1h"
  start_date: "2020-01-01"
  end_date: "2024-12-31"

# === Features ===
features:
  - name: rsi
    params: { period: 14 }
  - name: ema
    params: { period: 50 }
  - name: ema
    params: { period: 200 }
  - name: macd
    params: { fast: 12, slow: 26, signal: 9 }
  - name: bollinger_bands
    params: { period: 20, std_dev: 2 }
  - name: atr
    params: { period: 14 }
  - name: stochastic
    params: { k_period: 14, d_period: 3 }

# === Labeling ===
labeling:
  strategy: fixed_pip_threshold
  params:
    lookahead_bars: 5
    buy_threshold_pips: 10
    sell_threshold_pips: 10

# === Preprocessing ===
preprocessing:
  missing_data: drop        # drop | ffill | interpolate
  scaler: standard           # standard | minmax | robust | none

# === Split ===
split:
  method: time_based
  train_end_date: "2023-06-30"
  test_start_date: "2023-07-01"

# === Model ===
model:
  type: random_forest        # Looked up in model registry
  params:
    n_estimators: 200
    max_depth: 10
    min_samples_split: 5
    random_state: 42

# === Tracking ===
tracking:
  mlflow_tracking_uri: "http://localhost:5000"
  experiment_name: "forex_eurusd_1h"
```

---

## Project Structure

```
config-driven-forex-ml-pipeline/
├── pyproject.toml                    # Poetry config, dependencies, CLI entry point
├── poetry.lock
├── README.md
├── .env                              # DATABASE_URL, TWELVEDATA_API_KEY (gitignored)
├── .github/
│   └── workflows/
│       └── ci.yml                    # GitHub Actions: lint + test
├── configs/
│   └── example.yaml                  # Example training config
├── forex_pipeline/
│   ├── __init__.py
│   ├── cli/
│   │   ├── __init__.py
│   │   ├── app.py                    # Main Typer app
│   │   ├── data_cmd.py               # `data sync` command
│   │   └── train_cmd.py              # `train` command
│   ├── config/
│   │   ├── __init__.py
│   │   └── schema.py                 # Pydantic v2 config models
│   ├── data/
│   │   ├── __init__.py
│   │   ├── db.py                     # Postgres connection (SQLAlchemy)
│   │   ├── models.py                 # SQLAlchemy ORM models
│   │   ├── loader.py                 # Load data from DB into DataFrame
│   │   └── sync.py                   # TwelveData API → Postgres sync
│   ├── features/
│   │   ├── __init__.py
│   │   ├── registry.py               # Feature registry (decorator-based)
│   │   └── indicators.py             # Built-in feature functions
│   ├── labels/
│   │   ├── __init__.py
│   │   ├── registry.py               # Label strategy registry
│   │   └── strategies.py             # Built-in labeling strategies
│   ├── models/
│   │   ├── __init__.py
│   │   ├── registry.py               # Model registry
│   │   └── sklearn_models.py         # scikit-learn model wrappers
│   ├── preprocessing/
│   │   ├── __init__.py
│   │   └── pipeline.py               # Scaling, missing data handling
│   ├── tracking/
│   │   ├── __init__.py
│   │   └── mlflow_tracker.py         # MLflow logging wrapper
│   └── pipeline.py                   # Orchestrates the full training pipeline
├── tests/
│   ├── conftest.py                   # Shared pytest fixtures
│   ├── test_config.py                # Config validation tests
│   ├── test_features.py              # Feature function tests
│   ├── test_labels.py                # Labeling strategy tests
│   ├── test_preprocessing.py         # Preprocessing tests
│   ├── test_models.py                # Model registry tests
│   └── test_pipeline.py             # Integration tests
└── notebooks/
    └── twelvedata_check.ipynb        # Existing notebook
```

---

## Registry Pattern (Core Abstraction)

All extensible components (features, labels, models) follow the same registry pattern:

```python
# Example: Feature Registry
from typing import Callable, Dict, Any
import pandas as pd

_FEATURE_REGISTRY: Dict[str, Callable] = {}

def register_feature(name: str):
    """Decorator to register a feature function."""
    def decorator(func: Callable[[pd.DataFrame, Dict[str, Any]], pd.DataFrame]):
        _FEATURE_REGISTRY[name] = func
        return func
    return decorator

def get_feature(name: str) -> Callable:
    if name not in _FEATURE_REGISTRY:
        raise ValueError(f"Unknown feature: '{name}'. Available: {list(_FEATURE_REGISTRY.keys())}")
    return _FEATURE_REGISTRY[name]

# Usage:
@register_feature("rsi")
def compute_rsi(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    period = params.get("period", 14)
    # ... compute RSI ...
    df[f"rsi_{period}"] = rsi_values
    return df
```

The same pattern applies to labels (`@register_labeler`) and models (`@register_model`).

---

## Key Dependencies

| Package | Purpose |
|---|---|
| `typer[all]` | CLI framework |
| `rich` | Terminal UI (bundled with typer[all]) |
| `pydantic>=2.0` | Config validation |
| `pyyaml` | YAML parsing |
| `sqlalchemy>=2.0` | Postgres ORM |
| `psycopg2-binary` | Postgres driver |
| `python-dotenv` | Load `.env` file |
| `pandas` | Data manipulation |
| `numpy` | Numerical computing |
| `scikit-learn` | ML models |
| `ta` or `ta-lib` | Technical indicators (or hand-roll) |
| `mlflow` | Experiment tracking |
| `requests` | TwelveData API calls |
| `pytest` | Testing |
| `pytest-cov` | Coverage |
| `ruff` | Linting |

---

## v1 Scope

### In Scope
- [x] `forex-pipeline data sync` command (TwelveData → Postgres)
- [x] `forex-pipeline train --config config.yaml` command
- [x] YAML config with Pydantic v2 validation
- [x] Feature registry with 5-10 built-in technical indicators
- [x] Label registry with `fixed_pip_threshold` strategy
- [x] scikit-learn model registry (RandomForest, GradientBoosting)
- [x] Chronological train/test split
- [x] Feature scaling + missing data handling
- [x] MLflow experiment tracking
- [x] Rich terminal output
- [x] Tests + GitHub Actions CI

### Out of Scope (Future)
- [ ] `forex-pipeline backtest` command
- [ ] `forex-pipeline optimize` command (hyperparameter search)
- [ ] PyTorch deep learning models
- [ ] Walk-forward / purged k-fold splits
- [ ] Triple-barrier labeling
- [ ] Feature selection as a pipeline step
- [ ] Multi-pair training (train on multiple pairs simultaneously)

---

## Implementation Order

> [!IMPORTANT]
> Build in this order to ensure each step is testable before moving on.

1. **Project scaffolding** — Poetry setup, package structure, CI workflow
2. **Config schema** — Pydantic models for the full YAML config
3. **Database layer** — SQLAlchemy models, connection setup, migration
4. **Data sync** — TwelveData API client, `data sync` CLI command
5. **Feature registry** — Registry pattern + built-in indicators
6. **Label registry** — Registry pattern + `fixed_pip_threshold`
7. **Preprocessing** — Scaler + missing data handler
8. **Model registry** — Registry pattern + scikit-learn models
9. **Training pipeline** — Orchestrator that ties everything together
10. **MLflow tracking** — Log params, metrics, model, config
11. **`train` CLI command** — Wire up the pipeline to Typer
12. **Tests** — Unit + integration tests for all components
13. **Polish** — README, example configs, documentation
