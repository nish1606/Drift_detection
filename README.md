# Fraud Governance & Drift Detection System

An AI-based autonomous decision governance system for financial fraud detection — combining a real-time fraud-scoring model with drift detection, explainability, policy-driven governance, and a live monitoring dashboard.

Instead of just classifying transactions as fraud or not, this system continuously watches the *model itself*: detecting when its behavior drifts from what it learned in training, explaining why it makes the decisions it does, and automatically enforcing governance policies (alerting, falling back to safe rules, or freezing the model) when something looks wrong.

<p align="center">
  <em>React/Vite dashboard · FastAPI backend · Drift-aware fraud detection model</em>
</p>

<p align="center">
  <em>Final-year engineering major project</em>
</p>

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Project Layout](#project-layout)
- [Requirements](#requirements)
- [Dataset](#dataset)
- [Setup](#setup)
  - [Backend](#backend-setup)
  - [Frontend](#frontend-setup)
  - [Database](#database-setup)
  - [Run the Whole Project](#run-the-whole-project)
  - [Run with Docker (optional)](#run-with-docker-optional)
- [API Reference](#api-reference)
- [Dashboard Pages](#dashboard-pages)
- [How It Works](#how-it-works)
- [Tech Stack](#tech-stack)
- [Testing](#testing)
- [Known Limitations](#known-limitations)
- [License](#license)

---

## Overview

Fraud patterns change constantly, but most fraud-detection systems treat the model as a fixed, "set it and forget it" component. This project treats the model as something that needs **active governance**:

- **Detect** when incoming transaction patterns start looking statistically different from what the model was trained on (data drift, concept drift).
- **Explain** every flagged decision in terms a human reviewer can act on, not just a probability score.
- **Govern** the model against policy-as-code rules — thresholds for drift, confidence, and fairness that decide what happens next.
- **Respond** automatically to policy violations — alerting, recommending a retrain, or falling back to safer behavior — while keeping high-risk actions (redeploying a new model) gated behind human approval.
- **Monitor** all of the above on a live dashboard, with a full audit trail of every decision and every governance action taken.

## Architecture

```
Transaction → FastAPI /api/v1/predict → Fraud model → Prediction + confidence
                       │
                       ▼
                Decision logged (background task)
                       │
         ┌──────────────┼───────────────┐
         ▼              ▼               ▼
     Drift checks   Explainability   Risk scoring
    (/api/v1/summary) (/api/v1/explainability/grad-cam) (/api/v1/risk-score)
         └──────────────┬───────────────┘
                         ▼
               Governance policy engine
               (/api/v1/policies, /api/v1/decision)
                         │
                         ▼
           Alerts · Fallback · Freeze · Retrain flag
                         │
                         ▼
           Dashboard & audit log (/api/v1/dashboard, /api/v1/audit)
```

The frontend (`frontend/`) is a thin client — it reads from these APIs and renders them; all decisioning logic lives in the backend so it can be reasoned about, tested, and audited independently of the UI.

## Project Layout

```
Drift_detection/
├── backend/
│   ├── app.py               # FastAPI application factory and API wiring
│   ├── api/                 # Routers (auth, predict, predictions, transactions, drift, governance, monitoring, health)
│   ├── core/                # Config, exceptions, middleware, auth
│   ├── database/            # SQLAlchemy models, CRUD, engine
│   ├── detection/           # Drift detectors (statistical, semantic, concept)
│   ├── explainability/      # Grad-CAM attribution service
│   ├── governance/          # Policy engine, decision engine, risk scoring
│   ├── logging/             # Logger, decision logger
│   ├── model/               # Predictor, service, registry
│   ├── monitoring/          # Metrics, dashboard, audit
│   ├── preprocessing/       # Feature engineering
│   ├── response/            # Alerting, freeze, retraining, review queue
│   ├── schemas/             # Pydantic request/response models
│   ├── streaming/           # Live transaction stream generator
│   └── utils/               # Helpers, constants, validators
├── frontend/
│   ├── src/                 # React/Vite dashboard
│   ├── package.json
│   └── ...
├── ml_model/
│   ├── train.py             # Training script
│   ├── evaluate.py          # Evaluation utilities
│   ├── artifacts/           # Generated model artifacts (ignored by git)
│   └── data/                # Training data
│       └── transactions_realistic.csv
├── backend/data/
│   ├── transactions_realistic.csv   # Synthetic training data (20k rows)
│   └── mendeley/                     # Reference datasets for drift comparison
│       ├── harmonized_5000_temporally_matched.csv
│       ├── IEEE_selected_2000_final.csv
│       ├── PaySim_selected_2016_temporally_matched.csv
│       ├── ULB_selected_984_temporally_matched.csv
│       └── train_random_80.csv / test_random_20.csv
├── tests/                   # test suite
├── alembic/                 # database migrations
├── alembic.ini              # Alembic config
├── docker-compose.yml
├── Dockerfile
├── requirements.txt         # root-level Python dependencies
├── backend/requirements.txt # backend-specific Python dependencies
├── package.json             # frontend dependencies (in frontend/)
├── vite.config.js           # Vite config (in frontend/)
├── .gitignore
└── README.md
```

## Requirements

- Python 3.10+
- Node.js 18+
- `pip`

## Dataset

The repository includes synthetic training data and reference datasets for drift comparison:

- **Synthetic training data (included):** `backend/data/transactions_realistic.csv` ships with the repo. It contains 20,000 transactions with a 2.81% fraud class imbalance. This is the dataset the current `fraud_model.pkl` was trained on.

- **Reference datasets for drift comparison (included):** `backend/data/mendeley/` contains temporally-matched subsets from multiple real-world fraud datasets (IEEE-CIS, PaySim, ULB). These are used by the `/datasets/compare` endpoint to simulate and measure drift against the baseline training distribution. They are **not** used for model training.

If you want to experiment with additional training data, the original IEEE-CIS Fraud Detection dataset can be downloaded automatically:

```bash
python ml_model/download_data.py
```

This requires the Kaggle CLI (`pip install kaggle`) with your API credentials configured in `~/.kaggle/kaggle.json`. The downloaded files are placed in `ieee-fraud-detection/`, which is intentionally `.gitignore`d.

## Setup

### Backend Setup

Install the backend Python dependencies from the repository root:

```bash
pip install -r backend/requirements.txt
```

If you also want the root-level project dependencies:

```bash
pip install -r requirements.txt
```

Start the FastAPI backend:

```bash
uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000
```

Interactive API docs (Swagger UI) will be available at:

```
http://127.0.0.1:8000/docs
```

### Frontend Setup

Install frontend dependencies:

```bash
cd frontend && npm install
```

Run the Vite dev server:

```bash
cd frontend && npm run dev -- --host 127.0.0.1 --port 5173
```

### Database

The database is initialized automatically when the backend starts. To seed demo users, run:

```bash
python -m backend.data.seed_users
```

This inserts three demo accounts:
- **Analyst**: `analyst` / `analyst123`
- **Risk Engineer**: `risk_engineer` / `risk123`
- **Compliance**: `compliance` / `compliance123`

### Run the Whole Project

Use two terminals:

1. **Backend:** `uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000`
2. **Frontend:** `cd frontend && npm run dev -- --host 127.0.0.1 --port 5173`

Open the dashboard at:

```
http://127.0.0.1:5173/
```

Log in with one of the seeded accounts above.

**Note for Windows users:** The Vite dev proxy targets `127.0.0.1:8000` to avoid IPv6 resolution delays with `localhost`. If you change the backend host, update `frontend/vite.config.js` accordingly.

### Run with Docker (optional)

The Docker setup runs the **backend API only** against a PostgreSQL database. The frontend is not containerized; run it separately with `npm run dev` as described above.

```bash
docker-compose up --build
```

This does the following:
- Builds a Python image from `Dockerfile`
- Starts a PostgreSQL 16 container
- Starts the FastAPI backend on `http://localhost:8000`
- Auto-creates database tables on first startup

**After startup:**
- API docs: `http://localhost:8000/docs`
- Dashboard: Not served by Docker — use the Vite dev server instead

**Manual steps required inside the container:**

1. Seed demo users:
   ```bash
   docker-compose exec api python -m backend.data.seed_users
   ```

2. Train the model (or copy pre-trained artifacts into `ml_model/artifacts/`):
   ```bash
   docker-compose exec api python -m ml_model.train
   ```

**Environment variables:**
- `DATABASE_URL` — set in `docker-compose.yml` to `postgresql+psycopg2://postgres:postgres@postgres:5432/fraud_governance`
- `ENVIRONMENT` — set to `production` in `docker-compose.yml`

**Troubleshooting:**
- If the API crashes on startup with a PostgreSQL driver error, install `psycopg2-binary` in `backend/requirements.txt` and rebuild.
- If the dashboard loads but shows no data, the database may not be seeded — run the seed command above.
- If predictions return rule-based fallback scores instead of model outputs, no trained model artifacts are present — train the model or copy artifacts into `ml_model/artifacts/`.

## API Reference

All endpoints are versioned under `/api/v1/...`.

| Endpoint | Method | Auth | Description |
|---|---|---|---|
| `/api/v1/auth/login` | `POST` | No | Login with username/password, returns JWT token |
| `/api/v1/auth/register` | `POST` | No | Register a new user |
| `/api/v1/health` | `GET` | No | Service health check |
| `/api/v1/ready` | `GET` | No | Readiness check |
| `/api/v1/predict` | `POST` | Yes | Score a transaction and return a fraud prediction with confidence, risk score, and SHAP explanations |
| `/api/v1/predictions` | `GET` | Yes | Recent prediction history |
| `/api/v1/predictions/{prediction_id}` | `GET` | Yes | Single prediction detail |
| `/api/v1/transactions` | `GET` | Yes | Recent transactions with mapped status and SHAP values |
| `/api/v1/transactions/{request_id}/status` | `POST` | Yes | Update transaction review status |
| `/api/v1/policies` | `GET` | Yes | Governance policies |
| `/api/v1/policies/history` | `GET` | Yes | Policy change history |
| `/api/v1/policies/draft` | `POST` | Yes | Save a policy draft |
| `/api/v1/policies/evaluate` | `POST` | Yes | Evaluate policies against current data |
| `/api/v1/datasets` | `GET` | Yes | List available reference datasets |
| `/api/v1/datasets/compare` | `POST` | Yes | Compare two datasets for drift |
| `/api/v1/explainability/grad-cam` | `POST` | Yes | Tabular Grad-CAM attribution for a transaction |
| `/api/v1/explainability/shap` | `POST` | Yes | Signed SHAP attribution for a transaction |
| `/api/v1/explainability/lime` | `POST` | Yes | LIME attribution for a transaction |
| `/api/v1/dashboard` | `GET` | Yes | Aggregated dashboard metrics |
| `/api/v1/audit` | `GET` | Yes | Audit log entries |
| `/api/v1/summary` | `GET` | Yes | Drift summary, confidence trend, concept drift events |
| `/api/v1/drift/statistical` | `POST` | Yes | Run statistical drift detection on provided data |
| `/api/v1/drift/semantic` | `POST` | Yes | Run semantic/embedding drift detection |
| `/api/v1/drift/data-quality` | `POST` | Yes | Evaluate data quality metrics |
| `/api/v1/drift/concept` | `POST` | Yes | Update concept drift detector with new error values |
| `/api/v1/metrics` | `GET` | Yes | Protected metrics (Compliance / RiskEngineer only) |
| `/api/v1/decision` | `POST` | Yes | Record a governance decision |
| `/api/v1/risk-score` | `POST` | Yes | Compute risk score for a transaction |
| `/api/v1/summary` | `GET` | Yes | Drift summary, confidence trend, concept drift events |
| `/api/v1/drift/statistical` | `POST` | Yes | Run statistical drift detection on provided data |
| `/api/v1/drift/semantic` | `POST` | Yes | Run semantic/embedding drift detection |
| `/api/v1/drift/data-quality` | `POST` | Yes | Evaluate data quality metrics |
| `/api/v1/drift/concept` | `POST` | Yes | Update concept drift detector with new error values |
| `/api/v1/metrics` | `GET` | Yes | Protected metrics (Compliance / RiskEngineer only) |
| `/api/v1/decision` | `POST` | Yes | Record a governance decision |

Full interactive documentation is generated automatically by FastAPI at `/docs` once the backend is running.

### Authentication

The API uses JWT bearer tokens. Include the token in the `Authorization` header:

```
Authorization: Bearer <access_token>
```

Tokens are obtained via `POST /api/v1/auth/login` and expire after 30 minutes. Most endpoints require authentication; only `/health`, `/ready`, `/auth/login`, and `/auth/register` are public.

### Rate Limiting

Authenticated API requests are rate-limited to **60 requests per minute per IP address**. Exceeding this limit returns HTTP `429 Too Many Requests`.
The limit is configurable with `RATE_LIMIT_PER_MINUTE`. For benchmarks above 60 requests per minute, raise it (for example, `RATE_LIMIT_PER_MINUTE=100000`); this is a benchmarking setting only.

## Governance rules

Decisions are evaluated in this priority order:

1. policy block/freeze -> block
2. risk>=0.90 or drift>=0.90 -> freeze
3. risk>=0.75 or p>=0.95 -> block
4. risk>=0.45 or p>=0.60 -> review
5. allow

The risk formula is $R = \min(1, 0.65p + 0.20d + 0.10(1-q) + 0.05\pi + 0.10s)$, where $p$ is probability, $d$ is drift, $q$ is data quality, $\pi$ is policy penalty, and $s$ is the feature-risk signal. A policy `review` action alone does not change the decision.

The system has two PSI implementations: `StatisticalDriftDetector` uses quantile bins, while `dataset_comparison` uses equal-width bins and reports `normal`, `watch`, or `high`.

## Dashboard Pages

The React dashboard provides role-based views for analysts, risk engineers, and compliance teams:

- **Overview** — Model health gauge, live transaction flow, confidence/drift/fairness/explainability subscores, governance action feed, and story timeline
- **Review Queue** — Flagged transactions table with filters (date range, confidence threshold), detail panel with SHAP snapshot, and bulk status actions
- **Drift Monitoring** — Statistical drift, concept drift timeline, semantic drift, and distribution comparison charts
- **Explainability** — Global SHAP feature importance, local LIME explanations, and tabular Grad-CAM attribution heatmap for individual decisions
- **Fairness Monitoring** — Protected attribute segment analysis and demographic parity metrics
- **Policies** — Governance policy cards with version history and edit flows
- **Audit Log** — Full audit trail with search, filters, and exportable decision records

## How It Works

1. A transaction is sent to `POST /api/v1/predict`, which returns a fraud prediction, confidence score, risk score, decision, and SHAP-based explanations in real time. The prediction response is returned immediately; audit logging, alerting, and prediction-record writes are deferred to a background task so the client does not wait for database I/O.
2. Every prediction is logged to the database before any further processing happens, so nothing is lost even if a downstream step fails.
3. In the background, drift detectors compare recent transaction patterns against the distribution the model was trained on, surfaced via `GET /api/v1/summary`. Reference datasets for drift comparison are available under `backend/data/mendeley/` and can be compared via `POST /api/v1/datasets/compare`.
4. A governance policy engine evaluates drift, confidence, and fairness signals against configurable thresholds (`/api/v1/policies`, `/api/v1/policies/history`, `/api/v1/policies/draft`), deciding whether to alert, recommend a retrain, or trigger a safer fallback.
5. The dashboard (`frontend/`) fetches from `/api/v1/dashboard`, `/api/v1/predictions`, `/api/v1/audit`, and `/api/v1/summary` to render a live view of model health, flagged transactions, and governance history for analysts and risk teams. The Explainability page also calls `POST /api/v1/explainability/grad-cam` to render tabular Grad-CAM attributions for the selected transaction.

## Tech Stack

- **Frontend:** React, Vite, Chart.js
- **Backend:** FastAPI, Uvicorn, SQLAlchemy
- **Model:** scikit-learn pipeline with SHAP/LIME/Grad-CAM explainability
- **Database:** SQLite (local dev) / PostgreSQL (Docker) with Alembic migrations
- **Authentication:** JWT (python-jose)
- **Containerization:** Docker, Docker Compose
- **Testing:** pytest

## Testing

Run the test suite with:

```bash
pytest tests/
```

The suite covers API endpoints, authentication, drift detection, explainability, monitoring, policy engine, prediction pipeline, response handling, and training artifact generation.

## Known Limitations

- **CORS** is currently restricted to localhost development ports only and is not configured for external deployment.
- **Rate limiting** is per-IP, not per-token, so it is not suitable for multi-tenant production use as-is.
- **Authorization** uses role-based access control, but there is no scoped API key system — all authenticated users have equal access to all endpoints.
- **Explainability Loss** currently measures SHAP coverage only (presence of explanations), not explanation quality or stability over time.
- **Model provenance** is limited: `model_meta.pkl` stores only the model version, not the training dataset name, date, or class balance. Training artifacts (`fraud_model.pkl`, `baseline_stats.pkl`, `feature_columns.pkl`) are not tracked in git.
- **Grad-CAM** is available on the backend (`POST /api/v1/explainability/grad-cam`) and wired into the frontend Explainability page as a tabular attribution heatmap.
- **Dataset comparison** uses reference datasets under `backend/data/mendeley/` for drift simulation; these are not used for model training.

These are intentionally scoped out for this stage of the project and noted here for transparency.

## Experiment reproduction

Run `PYTHONPATH=. python run_experiments.py` to regenerate `results/experiment_results.json` and `EXPERIMENT_RESULTS.md`. The runner reports the paper-compatible legacy model and the optional scaled, threshold, chronological, semantic, data-quality, and explainability analyses side by side.


## License

This project is licensed under the [MIT License](LICENSE).
