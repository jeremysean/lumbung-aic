# Lumbung

Lumbung is a local-first AI replenishment copilot for growing independent retailers. A store owner uploads one `store_snapshot.csv`; Lumbung forecasts demand at P50 and P90, applies MOQ and stock constraints, then allocates purchase bundles under the store's hard budget limit.

The preliminary MVP intentionally implements one synchronous interaction. It has no login, database, background job, external API, automatic purchase order, or cloud dependency.

## Run with Docker Compose

Requirements: Docker Desktop with Docker Compose v2.

```bash
docker compose up --build
```

Wait until both services are healthy, then open:

- application: <http://localhost:3000>
- API health: <http://localhost:8000/health>
- interactive API contract: <http://localhost:8000/docs>

Download the sample CSV in the application, upload it unchanged, and click **Buat rencana belanja**. Stop the application with:

```bash
docker compose down
```

No environment variables or credentials are required.

## Core flow

```text
Browser (React)
  -> POST /v1/recommendations with one CSV
  -> strict schema and business-rule validation
  -> leakage-safe lag, rolling, and calendar features
  -> frozen LightGBM P50/P90 quantile models
  -> validation-calibrated P90 forecast
  -> target stock and MOQ rounding
  -> deterministic bounded-knapsack budget allocation
  -> numeric reasons, audit metadata, and downloadable CSV
```

The frontend and backend are separate containers. Nginx serves the static UI and proxies `/api/*` to FastAPI. Inference is synchronous and the trained artifacts are read-only.

## Input contract

The CSV must contain these exact columns:

| Column | Meaning | Validation |
|---|---|---|
| `date` | Daily observation date | Parseable date; unique per SKU |
| `sku_id` | Store SKU identifier | Non-empty; at least 28 observed days |
| `category` | Product category | Non-empty text |
| `sales_qty` | Units sold that day | Numeric and non-negative |
| `stock_on_hand` | Current units in store | Numeric and non-negative |
| `on_order` | Units already ordered | Numeric and non-negative |
| `unit_cost` | Purchase cost in IDR per unit | Numeric and non-negative |
| `unit_margin` | Expected margin in IDR per unit | Numeric and non-negative |
| `lead_time_days` | Supplier lead time | Integer of at least 1 |
| `moq` | Minimum order quantity in units | Integer of at least 1 |
| `available_budget` | Store purchase budget in IDR | One positive value repeated on every row |

The backend retains zero-sales days because intermittency is a model signal. It rejects missing values, negative values, duplicate `sku_id + date` pairs, inconsistent budgets, non-CSV uploads, and files over 10 MB with structured Problem Details responses.

## Output contract

Each SKU returns:

- P50 and P90 demand for `lead_time_days + 7` days;
- current stock, on-order stock, and stockout risk;
- deterministic `BELI_SEKARANG` or `TUNDA` decision;
- MOQ-compliant quantity and cost;
- numeric reason and priority score.

The complete response also includes budget utilization, model and parameter versions, data cutoff, review period, and a SHA-256 checksum of the normalized input. The owner remains responsible for approving every purchase.

## Model development and evidence boundary

The checked-in artifact is a fine-tuned LightGBM global quantile model. Tuning uses two expanding temporal folds. Evaluation uses a later untouched temporal test containing 432 examples. The P90 offset is selected on a pre-test calibration window.

| Metric | Fine-tuned model | Moving-average baseline |
|---|---:|---:|
| Mean P50/P90 pinball loss | 1.786392 | 1.828699 |
| P50 WAPE | 0.200564 | 0.205738 |
| P90 coverage | 0.891204 | N/A |

These results are from deterministic **synthetic retail history** and establish only that the software pipeline and acceptance gate work in the supplied test regime. They do not prove stockout reduction, savings, product-market fit, or transfer to Indonesian retail data. See [MODEL_CARD.md](MODEL_CARD.md) and `artifacts/model_metadata.json` for the full parameters, data hash, folds, and limitations.

## Reproduce training and tests

Python 3.12 or 3.13 is recommended.

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -r backend/requirements-dev.txt
python scripts/generate_demo_data.py
python scripts/train_model.py
$env:PYTHONPATH="backend"  # macOS/Linux: export PYTHONPATH=backend
python -m pytest backend/tests -q --cov=backend/app
python -m ruff check backend scripts
```

Frontend verification:

```bash
cd frontend
npm ci
npm run build
```

Training is deterministic for the fixed data generator, version pins, and seed. `trained_at_utc` is expected to change between runs; predictions and reported metrics must not.

## Repository map

```text
artifacts/                 Frozen models and machine-readable model metadata
backend/app/               Validation, feature, inference, optimizer, and API modules
backend/tests/             Unit and contract tests
data/                      Synthetic training history and upload-ready example
frontend/                  Focused React upload and recommendation interface
scripts/                   Deterministic data generation and temporal model tuning
docker-compose.yml         Local two-container runtime
SUBMISSION_CHECKLIST.md    AIC deliverable and compliance status
```

## Known limitations

- Synthetic demand is not representative evidence for any real store population.
- POS zero sales may be censored by stockouts; no availability flag is currently available.
- P90 coverage is close to, but not exactly, 90% on the synthetic holdout.
- No field pilot, local POS integration, expiry model, or supplier reliability model is included.
- The bundled Google font request improves typography when online; system fonts preserve all functionality offline.

## Responsible use

Lumbung never sends a purchase automatically. Budget is a hard constraint, recommendations are reproducible, and all reasons are generated from numeric model and inventory outputs rather than an LLM. Before a real pilot, remove customer identifiers from exports, obtain store consent, validate inventory accuracy, and retrain and recalibrate on an authorized local dataset.

