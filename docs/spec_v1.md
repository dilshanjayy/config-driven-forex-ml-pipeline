# Config-Driven Forex ML Pipeline — v1 Spec

## Problem Statement

A forex ML practitioner wants to rapidly experiment with different combinations of technical indicators, labeling strategies, preprocessing approaches, and models — but each experiment currently requires writing and modifying Python scripts by hand. There is no structured way to define an experiment as configuration, run it reproducibly, and compare results across runs. This slows down iteration and makes it hard to track what was tried and what worked.

## Solution

A CLI tool (`fxml`) that reads a YAML config file specifying every aspect of a training experiment — data range, features, labeling strategy, preprocessing, split method, and model — validates it, executes the full training pipeline, and produces a self-contained run directory with the trained model, fitted scaler, and evaluation metrics. The tool provides discovery commands to list available components, a run history view, and a separate evaluation command for testing saved models. All OHLCV data is stored in PostgreSQL, with a centralized AWS Lambda handling daily data sync from TwelveData and users having read-only database access.

## User Stories

1. As a forex ML practitioner, I want to define my entire training experiment in a single YAML file, so that I can reproduce and share experiments without explaining code changes.
2. As a forex ML practitioner, I want the tool to validate my config before training starts, so that I catch typos and invalid parameters immediately rather than mid-run.
3. As a forex ML practitioner, I want to run `fxml train --dry-run` to see what the pipeline would do (data shape, class distribution, split sizes) without actually training, so that I can verify my config is sensible.
4. As a forex ML practitioner, I want to specify which technical indicators to use as features with their parameters (e.g., RSI with period 14, EMA with period 200), so that I can experiment with different feature combinations without writing code.
5. As a forex ML practitioner, I want the same feature name with different parameters (e.g., two EMAs with different periods) to produce distinctly named columns, so that I can include multiple variations of the same indicator.
6. As a forex ML practitioner, I want to specify a labeling strategy and its parameters in config (e.g., fixed pip threshold with 10-pip buy/sell thresholds and 5-bar lookahead), so that I can experiment with different label definitions.
7. As a forex ML practitioner, I want pip thresholds to be automatically resolved to the correct price delta based on the pair (0.0001 for most pairs, 0.01 for JPY pairs), so that I don't have to manually convert pips to price deltas.
8. As a forex ML practitioner, I want to choose a model type and its hyperparameters in config (e.g., RandomForest with n_estimators=200), so that I can compare different models on the same data and features.
9. As a forex ML practitioner, I want to set `class_weight: balanced` in my model config, so that I can address class imbalance without resampling.
10. As a forex ML practitioner, I want the pipeline to always show class distribution (buy/sell/hold counts and percentages) before training, so that I can detect imbalance and adjust thresholds if needed.
11. As a forex ML practitioner, I want the pipeline to warn me when class imbalance is detected (any class below 20% or above 60%), so that I'm aware of potential bias.
12. As a forex ML practitioner, I want to split my data chronologically using a single split date, so that I can evaluate my model on future data without temporal leakage.
13. As a forex ML practitioner, I want to optionally define a 3-way split (train/validation/test) by adding a test date, so that I can tune hyperparameters on the validation set without contaminating my test evaluation.
14. As a forex ML practitioner, I want the embargo (gap between train and validation/test) to be automatically calculated from my labeling strategy's lookahead bars, so that label lookahead leakage is prevented without manual configuration.
15. As a forex ML practitioner, I want test metrics hidden by default when a validation set is present, so that I don't accidentally leak test information through my own iterative decision-making.
16. As a forex ML practitioner, I want to use `--eval` to explicitly reveal test metrics when I'm done iterating, so that I get an honest final evaluation.
17. As a forex ML practitioner, I want to run `fxml eval --run <run_name>` to evaluate a previously trained model on the test set without retraining, so that I can go back and evaluate earlier runs I'm now interested in.
18. As a forex ML practitioner, I want the pipeline to automatically fetch extra warm-up data before my requested start date (if available in the database), so that lagged indicators have enough history and I don't lose usable rows from my training range.
19. As a forex ML practitioner, I want structural NaN rows from the warm-up period to be automatically trimmed (never configurable), so that indicators with insufficient lookback don't produce garbage values.
20. As a forex ML practitioner, I want a separate, configurable strategy (drop/ffill/interpolate) for handling gap NaNs in the middle of my data, so that I can choose how to deal with genuine data gaps.
21. As a forex ML practitioner, I want the scaler to be fit only on the training set and then used to transform all sets, so that test/validation data doesn't leak into scaling statistics.
22. As a forex ML practitioner, I want each training run to produce a self-contained directory with the config, model, scaler, and metrics, so that any run can be reproduced or evaluated later.
23. As a forex ML practitioner, I want to see macro F1 as the headline metric (not accuracy), along with per-class precision/recall/F1, confusion matrix, and class distribution, so that I can properly evaluate a multi-class model with potential imbalance.
24. As a forex ML practitioner, I want to run `fxml list features` to see all available feature functions and their parameters, so that I know what to put in my config without reading source code.
25. As a forex ML practitioner, I want to run `fxml list labels` to see all available labeling strategies, so that I know my options.
26. As a forex ML practitioner, I want to run `fxml list models` to see all available model types and their parameters, so that I know what models I can configure.
27. As a forex ML practitioner, I want to run `fxml list runs` to see a summary table of all past runs (date, pair, model, val F1, test F1), so that I can compare experiments at a glance.
28. As a forex ML practitioner, I want `fxml list runs` to show "—" for test F1 when a run hasn't been evaluated with `--eval`, so that I can tell which runs have honest test evaluations.
29. As a forex ML practitioner, I want the run name to be auto-generated from the timestamp, pair, and model type if I don't provide `--run-name`, so that runs are identifiable without manual naming.
30. As a developer, I want to run `fxml sync --pair EUR/USD --interval 1h` to populate my local Postgres with OHLCV data during development, so that I can test the pipeline without depending on the Lambda.
31. As a developer, I want the sync command to do incremental sync (only fetching data after the latest existing timestamp), so that repeated syncs are fast and don't waste API calls.
32. As an admin, I want the Lambda to read its sync configuration (pairs and intervals) from a JSON/YAML file in S3, so that I can add or remove pairs without redeploying the Lambda.
33. As an admin, I want users to have read-only database access, so that they cannot accidentally corrupt shared OHLCV data.
34. As a developer, I want to run the project locally with `docker-compose up` to get a Postgres instance, so that I don't need to install Postgres manually.
35. As a developer, I want database schema changes managed by Alembic migrations, so that schema evolution is tracked and reproducible.
36. As a developer, I want to add a new feature function by writing a decorated Python function in the indicators module, so that extending the tool doesn't require modifying framework code.
37. As a developer, I want to add a new labeling strategy by writing a decorated function in the strategies module, so that new strategies follow the same pattern as features.
38. As a developer, I want to add a new model by writing a decorated function in the sklearn_models module, so that new models are automatically available in the config.
39. As a developer, I want the pipeline to show Rich-formatted progress output at each stage (config validated, data loaded, features computed, labels computed, split applied, training, metrics), so that I can see what's happening during a run.
40. As a developer, I want pre-flight checks to run before any heavy computation (data exists, registry names valid, split date in range, unique feature/param tuples), so that obvious errors fail fast with clear messages.

## Implementation Decisions

### CLI Structure
- CLI tool is named `fxml`, built with Typer + Rich.
- Four top-level commands: `sync`, `train`, `eval`, `list`.
- `train` accepts `--config` (required), `--run-name` (optional, auto-generated if omitted as `{timestamp}_{pair}_{model_type}`), `--dry-run` (optional), `--eval` (optional, reveals test metrics).
- `eval` accepts `--run` (required, the run directory name).
- `list` accepts a subcommand: `features`, `labels`, `models`, or `runs`.

### Config Schema
- YAML config validated via Pydantic v2 models.
- Sections: `data`, `features`, `labeling`, `preprocessing`, `split`, `model`, `tracking`.
- `split.split_date` is required. `split.test_date` is optional (enables 3-way split). `split.embargo_bars` is optional (auto-derived from `labeling.params.lookahead_bars` if omitted).
- Pydantic validation must enforce: `split_date` within data date range; `test_date` after `split_date` if provided; each `(feature.name, feature.params)` tuple is unique; all registry names exist.

### Registry Pattern
- Features, labels, and models all use the same decorator-based registry pattern: a module-level dict mapping string names to callables.
- Each registry entry carries metadata (description, parameter names/defaults) for the `fxml list` command.
- Feature functions receive the full OHLCV DataFrame, mutate it by adding their computed columns, and return it (mutate-and-pass-through contract). Feature functions own their column naming.
- The pipeline orchestrator validates that no two feature calls produce duplicate column names.

### Labeling
- `fixed_pip_threshold` strategy: compares close price at T+`lookahead_bars` to close at T. If delta >= `buy_threshold_pips` (in pip units) → buy, if delta <= negative `sell_threshold_pips` → sell, else → hold.
- A `pip_size(pair)` utility resolves pip to price delta: 0.01 for JPY pairs, 0.0001 for all others.

### Pipeline Ordering
- The pipeline executes in strict order: fetch data (with warm-up) → compute features → compute labels → trim warm-up → trim to date range → show class distribution → split (with embargo) → fit scaler on train only → transform all sets → train model → evaluate and report.
- This ordering prevents data leakage from scaler fitting and label lookahead.

### Two-Stage NaN Handling
- Stage 1 (warm-up trimming): automatic, always applied. After feature computation, calculate max lookback across all features and drop that many rows from the top. Non-configurable.
- Stage 2 (gap handling): configurable via `preprocessing.missing_data`. Only applies to NaNs remaining after warm-up trimming. Options: `drop`, `ffill`, `interpolate`.

### Warm-up Data Fetching
- When loading data, the loader queries for extra rows before `data.start_date` equal to the max feature lookback, if available in the database. After feature computation and warm-up trimming, the data is trimmed to the user's requested date range.

### Scaler
- Fit on train set only, transform train/validation/test. Scaler type configured via `preprocessing.scaler`: `standard`, `minmax`, `robust`, or `none`.
- Saved as `scaler.joblib` in the run directory for use by `fxml eval`.

### Splitting
- 2-way split: single `split_date` separates train and test. Test metrics shown directly.
- 3-way split: `split_date` separates train and validation, `test_date` separates validation and test. Test metrics hidden unless `--eval` is passed.
- Embargo applied at each boundary, default value = `labeling.params.lookahead_bars`, overridable via `split.embargo_bars`.

### Test Metric Hiding
- When a 3-way split is configured, `fxml train` only shows validation metrics by default. Test metrics are still computed and saved to `metrics.json` but not printed.
- `--eval` flag on `train` reveals test metrics. `fxml eval --run` also reveals test metrics.
- `fxml list runs` shows val F1 for all runs, and test F1 only for runs that were evaluated with `--eval` or `fxml eval`.

### Run Output
- Each run produces a directory under `runs/` named with the auto-generated or user-provided run name.
- Contents: `config.yaml` (exact config snapshot), `model.joblib` (trained model), `scaler.joblib` (fitted scaler), `metrics.json` (all metrics for all evaluated sets).

### Metrics
- Headline metric: macro F1.
- Per-class: precision, recall, F1, support.
- Confusion matrix.
- Class distribution (counts and percentages) for each set.
- Accuracy (secondary).

### Models (v1)
- RandomForestClassifier, GradientBoostingClassifier, LogisticRegression via scikit-learn.
- Model interface follows scikit-learn's `fit(X, y)` / `predict(X)` API.
- XGBoost added after core models are working (separate dependency).
- PyTorch models are out of scope for v1.

### Features (v1)
- Built-in indicators via pandas-ta: RSI, EMA, MACD, Bollinger Bands, ATR, Stochastic.
- Users extend by adding decorated functions in the indicators module (no plugin system for v1).

### Data Layer
- PostgreSQL with SQLAlchemy ORM. Schema: single `ohlcv` table with `UNIQUE(pair, interval, timestamp)`.
- Alembic for migrations.
- Connection via `DATABASE_URL` environment variable (works for both local and AWS RDS).

### Data Sync
- Sync module shared between `fxml sync` CLI command (dev/admin) and Lambda handler.
- Incremental sync: queries latest timestamp per pair/interval, fetches only newer data from TwelveData.
- Simple rate limiting via `time.sleep()` between API requests.
- Lambda runs daily on CloudWatch schedule, reads pair/interval config from S3.
- Users have read-only DB access in production; only Lambda writes.

### Initial Pair/Interval Support
- 7 major forex pairs: EUR/USD, GBP/USD, USD/JPY, USD/CHF, AUD/USD, USD/CAD, NZD/USD.
- 2 intervals: 1h, 1day (14 combinations).

### Infrastructure
- Docker Compose for local development (Postgres).
- Terraform for AWS infrastructure: RDS, Lambda, S3, IAM roles, CloudWatch schedule.
- Monorepo layout: CLI tool, Lambda handler, and Terraform configs all in one repository.

### MLflow
- Deferred to late in v1. Pipeline built with local run directories first.
- When integrated, logs params, metrics, model artifacts, and config to MLflow tracking server.

## Testing Decisions

### What makes a good test
- Tests should assert **external behavior**, not implementation details. A test should not care how a feature function computes RSI internally — it should care that given an OHLCV DataFrame with known values, the output DataFrame has the expected column with values in the expected range.
- Tests should use real DataFrames with realistic (but small) data, not excessive mocking.

### Testing seams
- **Pipeline orchestrator** (highest seam): integration test takes a config dict and a DataFrame, runs the full pipeline, and asserts a valid run directory is produced with expected metrics structure.
- **Config schema**: unit test constructs Pydantic models directly — valid configs parse, invalid configs raise `ValidationError` with clear messages.
- **Feature registry**: unit test passes a small OHLCV DataFrame, asserts expected columns are added with correct names and no NaN in the non-warm-up region.
- **Label registry**: unit test passes an OHLCV DataFrame with known prices, asserts labels are exactly buy/sell/hold with correct assignments based on the threshold logic.
- **Preprocessing pipeline**: unit test passes a DataFrame with intentional NaNs (warm-up and gap), asserts warm-up rows are trimmed and gap handling applies correctly. Separate test for scaler fit-on-train-only behavior.
- **Model registry**: unit test fits a model on small X/y, asserts `predict` returns correct output shape and valid class labels.
- **Data loader**: integration test (requires Docker Postgres) inserts known OHLCV rows, queries them back, asserts correct DataFrame shape and content.
- **Sync module**: integration test (requires Docker Postgres) runs sync with mocked API responses, asserts rows are upserted correctly and incremental sync skips existing data.

### Test infrastructure
- Unit tests run without any external dependencies (no database, no API calls). They use in-memory DataFrames.
- Integration tests require a running Postgres instance, provided by Docker Compose. CI runs these with a Postgres service container in GitHub Actions.
- pytest + pytest-cov for test execution and coverage.

## Out of Scope

- **`fxml optimize` command** — automated hyperparameter search over validation set. Manual iteration via `fxml train` is the v1 workflow.
- **PyTorch deep learning models** — model interface is scikit-learn `fit`/`predict` for v1.
- **Walk-forward and purged k-fold splits** — only chronological (2-way or 3-way) splits are supported.
- **Triple-barrier labeling** — only `fixed_pip_threshold` (close-to-close) is implemented. The label registry supports adding new strategies.
- **Feature selection as a pipeline step** — users manually choose features in config.
- **Multi-pair training** — training on multiple pairs simultaneously in a single run.
- **`fxml backtest` command** — backtesting with simulated trades and P&L.
- **Plugin system for external features/labels/models** — extensibility is via editing the package source, not external plugins.
- **Real-time data sync** — Lambda runs daily; sub-daily refresh is not supported.
- **Caching layer** — no local caching of database queries.

## Further Notes

- The project serves dual purposes: (A) a reusable experimentation tool for rapid iteration on forex ML strategies, and (B) a portfolio piece demonstrating industry-standard technologies (PostgreSQL, Alembic, AWS Lambda/RDS/S3, Terraform, Docker, MLflow, CI/CD).
- The domain glossary is maintained in `CONTEXT.md` at the project root. All code, config, and documentation should use the canonical terms defined there (e.g., "pair" not "symbol", "feature" not "indicator" in pipeline context, "run" not "experiment").
- Architectural decisions are recorded in `docs/adr/`. Currently: ADR-0001 (PostgreSQL over Parquet) and ADR-0002 (centralized data sync via Lambda).

---

## Reference: Architecture Decisions

| Decision | Choice |
|---|---|
| Language | Python |
| Config format | YAML |
| Config validation | Pydantic v2 |
| CLI framework | Typer + Rich |
| CLI name | `fxml` |
| Data storage | PostgreSQL (AWS RDS for production, local for dev) |
| DB migrations | Alembic |
| Data ingestion | TwelveData API → Postgres (centralized Lambda, daily) |
| Feature engineering | Registry pattern, pandas-ta, mutate-and-pass-through |
| Labeling | Registry pattern, pip-size resolved per pair |
| Models | Pluggable registry — scikit-learn first (RF, GB, LR), then XGBoost |
| Model interface | scikit-learn `fit`/`predict` API |
| Prediction task | Classification (buy / sell / hold) |
| Train/test split | Chronological split, optional 3-way (train/val/test) |
| Embargo | Auto-derived from labeling `lookahead_bars` |
| Preprocessing | Warm-up trimming (auto) → gap handling (configurable) → scaler (fit on train only) |
| Experiment tracking | Local run directories first, MLflow later |
| Headline metric | Macro F1 (not accuracy) |
| Packaging | Poetry + pyproject.toml |
| Testing | pytest (unit: no DB, integration: real Postgres via Docker) |
| CI | GitHub Actions |
| Terminal output | Rich (progress bars, tables, colored logs) |
| DB connection | `DATABASE_URL` env var (python-dotenv) |
| Infrastructure | Docker Compose (local dev), Terraform (AWS: RDS, Lambda, S3, IAM) |
| Project layout | Monorepo |

---

## Reference: Database Schema

```sql
CREATE TABLE ohlcv (
    id          BIGSERIAL PRIMARY KEY,
    pair        VARCHAR(10) NOT NULL,     -- e.g. 'EUR/USD'
    interval    VARCHAR(5)  NOT NULL,     -- e.g. '1h', '1d'
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

## Reference: Example Config (`config.yaml`)

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
    buy_threshold_pips: 10      # resolved to price delta per pair
    sell_threshold_pips: 10

# === Preprocessing ===
preprocessing:
  missing_data: drop             # drop | ffill | interpolate (for gap NaNs only)
  scaler: standard               # standard | minmax | robust | none

# === Split ===
split:
  method: time_based
  split_date: "2023-01-01"       # train/validation boundary
  # test_date: "2023-07-01"      # optional: validation/test boundary (enables 3-way split)
  # embargo_bars: auto            # auto-derived from lookahead_bars, or set manually

# === Model ===
model:
  type: random_forest             # looked up in model registry
  params:
    n_estimators: 200
    max_depth: 10
    min_samples_split: 5
    class_weight: balanced        # balanced | null
    random_state: 42

# === Tracking ===
tracking:
  mlflow_tracking_uri: "http://localhost:5000"    # used when MLflow is enabled
  experiment_name: "forex_eurusd_1h"
```

---

## Reference: Split Modes

### 2-way split (only `split_date`)
```
|---------- Train ----------|-------- Test --------|
start_date            split_date              end_date
```
- Test metrics shown directly (no hiding)

### 3-way split (`split_date` + `test_date`)
```
|------- Train -------|-- Val --|------ Test ------|
start_date       split_date  test_date         end_date
```
- Validation metrics shown by default
- Test metrics hidden unless `--eval` flag is used
- Embargo applied at both boundaries

---

## Reference: Run Output

Each training run produces a self-contained directory:

```
runs/
  2026-07-12_10-30_EUR-USD_random-forest/
    config.yaml          # exact config used
    model.joblib         # trained model
    scaler.joblib        # fitted scaler
    metrics.json         # all evaluation metrics
```

---

## Reference: Metrics

| Metric | Purpose |
|---|---|
| **Macro F1** (headline) | Primary "is this model any good" metric — treats all classes equally |
| Precision per class | When model says "buy", how often is it right? |
| Recall per class | Of all real buy opportunities, how many caught? |
| F1 per class | Balance of precision and recall per class |
| Confusion matrix | What's being confused with what |
| Class distribution | Train/val/test label counts and percentages |
| Accuracy | Secondary metric (misleading with imbalanced classes) |

---

## Reference: Supported Pairs and Intervals

| Pair | Pip Size |
|---|---|
| EUR/USD | 0.0001 |
| GBP/USD | 0.0001 |
| USD/JPY | 0.01 |
| USD/CHF | 0.0001 |
| AUD/USD | 0.0001 |
| USD/CAD | 0.0001 |
| NZD/USD | 0.0001 |

Intervals: `1h`, `1day` (14 combinations total). Expand based on API limits.

---

## Reference: Project Structure

```
config-driven-forex-ml-pipeline/
├── pyproject.toml                    # Poetry config, dependencies, CLI entry point
├── poetry.lock
├── README.md
├── CONTEXT.md                        # Domain glossary
├── .env                              # DATABASE_URL, TWELVEDATA_API_KEY (gitignored)
├── docker-compose.yml                # Local dev: Postgres
├── Dockerfile                        # Lambda packaging
├── .github/
│   └── workflows/
│       └── ci.yml                    # GitHub Actions: lint + test
├── configs/
│   └── example.yaml                  # Example training config
├── lambda/
│   └── handler.py                    # Lambda entry point (imports sync module)
├── terraform/
│   ├── main.tf                       # RDS, Lambda, S3, IAM, CloudWatch
│   ├── variables.tf
│   └── outputs.tf
├── docs/
│   └── adr/
│       ├── 0001-postgres-over-parquet.md
│       └── 0002-centralized-data-sync-via-lambda.md
├── forex_pipeline/
│   ├── __init__.py
│   ├── cli/
│   │   ├── __init__.py
│   │   ├── app.py                    # Main Typer app
│   │   ├── sync_cmd.py              # `sync` command
│   │   ├── train_cmd.py              # `train` command
│   │   ├── eval_cmd.py               # `eval` command
│   │   └── list_cmd.py               # `list` command
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
│   │   └── indicators.py             # Built-in feature functions (pandas-ta)
│   ├── labels/
│   │   ├── __init__.py
│   │   ├── registry.py               # Label strategy registry
│   │   ├── strategies.py             # Built-in labeling strategies
│   │   └── pip_utils.py              # Pip-size resolver per pair
│   ├── models/
│   │   ├── __init__.py
│   │   ├── registry.py               # Model registry
│   │   └── sklearn_models.py         # scikit-learn model wrappers (RF, GB, LR)
│   ├── preprocessing/
│   │   ├── __init__.py
│   │   └── pipeline.py               # Warm-up trimming, gap handling, scaling
│   ├── tracking/
│   │   ├── __init__.py
│   │   └── mlflow_tracker.py         # MLflow logging wrapper (deferred)
│   └── pipeline.py                   # Orchestrates the full training pipeline
├── migrations/
│   └── ...                           # Alembic migration scripts
├── runs/                             # Training run outputs
├── tests/
│   ├── conftest.py                   # Shared pytest fixtures
│   ├── test_config.py                # Config validation tests
│   ├── test_features.py              # Feature function tests
│   ├── test_labels.py                # Labeling strategy tests
│   ├── test_preprocessing.py         # Preprocessing tests
│   ├── test_models.py                # Model registry tests
│   └── test_pipeline.py              # Integration tests (requires Postgres)
└── notebooks/
    └── twelvedata_check.ipynb        # Existing notebook
```

---

## Reference: Key Dependencies

| Package | Purpose |
|---|---|
| `typer[all]` | CLI framework |
| `rich` | Terminal UI (bundled with typer[all]) |
| `pydantic>=2.0` | Config validation |
| `pyyaml` | YAML parsing |
| `sqlalchemy>=2.0` | Postgres ORM |
| `psycopg2-binary` | Postgres driver |
| `alembic` | Database migrations |
| `python-dotenv` | Load `.env` file |
| `pandas` | Data manipulation |
| `numpy` | Numerical computing |
| `scikit-learn` | ML models |
| `pandas-ta` | Technical indicators |
| `joblib` | Model/scaler serialization |
| `mlflow` | Experiment tracking (deferred) |
| `requests` | TwelveData API calls |
| `pytest` | Testing |
| `pytest-cov` | Coverage |
| `ruff` | Linting |
| `xgboost` | XGBoost model (added after core models) |

---

## Reference: Implementation Order

> [!IMPORTANT]
> Build in this order to ensure each step is testable before moving on.

| Phase | Step | What |
|---|---|---|
| **Foundation** | 1 | Project scaffolding — Poetry, package structure, Docker Compose, CI |
| | 2 | Config schema — Pydantic models for the full YAML config |
| | 3 | Database layer — SQLAlchemy models, Alembic migrations |
| **Data** | 4 | Sync module — TwelveData API client, `fxml sync` CLI command |
| **Core Pipeline** | 5 | Feature registry + built-in indicators (pandas-ta) |
| | 6 | Label registry + `fixed_pip_threshold` (with pip-size resolver) |
| | 7 | Preprocessing — warm-up trimming, gap handling, scaler (fit on train only) |
| | 8 | Model registry — RF, GradientBoosting, LogisticRegression |
| | 9 | Training pipeline orchestrator (full pipeline flow) |
| **CLI** | 10 | `fxml train` command (with --dry-run, --eval, --run-name) |
| | 11 | `fxml list` command (features, labels, models, runs) |
| | 12 | `fxml eval` command |
| **Tracking** | 13 | MLflow integration |
| **Infrastructure** | 14 | Lambda sync service + Terraform (RDS, Lambda, S3, IAM) |
| **Quality** | 15 | XGBoost model |
| | 16 | Tests — unit + integration |
| | 17 | Polish — README, example configs, documentation |
