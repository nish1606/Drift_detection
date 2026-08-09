# Fraud Governance & Drift Detection System

An AI-based autonomous decision governance system for financial fraud detection — combining a real-time fraud-scoring model with drift detection, explainability, policy-driven governance, and a live monitoring dashboard.

Instead of just classifying transactions as fraud or not, this system continuously watches the *model itself*: detecting when its behavior drifts from what it learned in training, explaining why it makes the decisions it does, and automatically enforcing governance policies (alerting, falling back to safe rules, or freezing the model) when something looks wrong.

<p align="center">
  <em>React/Vite dashboard · FastAPI backend · Drift-aware fraud detection model</em>
</p>

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Project Layout](#project-layout)
- [Requirements](#requirements)
- [Setup](#setup)
  - [Backend](#backend-setup)
  - [Frontend](#frontend-setup)
  - [Database](#database-setup)
  - [Run the Whole Project](#run-the-whole-project)
- [API Reference](#api-reference)
- [Dashboard Pages](#dashboard-pages)
- [How It Works](#how-it-works)
- [Tech Stack](#tech-stack)
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
               Decision logged
                      │
        ┌──────────────┼───────────────┐
        ▼              ▼               ▼
    Drift checks   Explainability   Risk scoring
   (/api/v1/summary)              (/api/v1/governance)
        └──────────────┬───────────────┘
                        ▼
              Governance policy engine
                        │
                        ▼
          Alerts · Fallback · Freeze · Retrain flag
                        │
                        ▼
          Dashboard & audit log (/api/v1/monitoring)
```

The frontend (`frontend/`) is a thin client — it reads from these APIs and renders them; all decisioning logic lives in the backend so it can be reasoned about, tested, and audited independently of the UI.

## Project Layout

```
Drift_detection/
├── backend/
│   ├── app.py               # FastAPI application factory and API wiring
│   ├── api/                 # Routers (predict, drift, governance, monitoring, health, auth)
│   ├── core/                # Config, exceptions, middleware, auth
│   ├── database/            # SQLAlchemy models, CRUD, engine
│   ├── detection/           # Drift detectors (statistical, semantic, concept)
│   ├── explainability/      # SHAP/LIME services
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
│   ├── train.py             # Training script (writes artifacts to ml_model/artifacts/)
│   ├── evaluate.py          # Evaluation utilities
│   ├── artifacts/           # Generated model artifacts (ignored by git)
│   └── data/                # Training data
│       └── transactions_synthetic.csv
├── tests/                   # test suite
├── alembic/                 # database migrations
├── alembic.ini              # Alembic config
├── docker-compose.yml
├── Dockerfile
├── requirements.txt         # root-level Python dependencies
├── backend/requirements.txt # backend-specific Python dependencies
├── package.json             # frontend dependencies
├── vite.config.js
├── .gitignore
└── README.md
```

## Requirements

- Python 3.10+
- Node.js 18+
- `pip`

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

### Database Setup

Initialize the SQLite database and seed demo users:

```bash
cd backend
python -m database.init_db
python -m data.seed_users
```

This creates the database file and inserts three demo accounts:
- **Analyst**: `analyst` / `analyst123`
- **Risk Engineer**: `risk_engineer` / `risk123`
- **Compliance**: `compliance` / `compliance123`

### Frontend Setup

Install frontend dependencies:

```bash
cd frontend && npm install
```

### Run the Whole Project

Use two terminals:

1. **Backend:** `uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000`
2. **Frontend:** `cd frontend && npm run dev -- --host 127.0.0.1 --port 5173`

Open the dashboard at:

```
http://127.0.0.1:5173/
```

Log in with one of the seeded accounts above.

### Run with Docker (optional)

```bash
docker-compose up --build
```

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
| `/api/v1/policies` | `GET` | Yes | Governance policies |
| `/api/v1/dashboard` | `GET` | Yes | Aggregated dashboard metrics |
| `/api/v1/audit` | `GET` | Yes | Audit log entries |
| `/api/v1/summary` | `GET` | Yes | Drift summary, confidence trend, concept drift events |
| `/api/v1/drift/statistical` | `POST` | Yes | Run statistical drift detection on provided data |
| `/api/v1/drift/semantic` | `POST` | Yes | Run semantic/embedding drift detection |
| `/api/v1/drift/data-quality` | `POST` | Yes | Evaluate data quality metrics |
| `/api/v1/drift/concept` | `POST` | Yes | Update concept drift detector with new error values |
| `/api/v1/metrics` | `GET` | Yes | Protected metrics (Compliance / RiskEngineer only) |

Full interactive documentation is generated automatically by FastAPI at `/docs` once the backend is running.

### Authentication

The API uses JWT bearer tokens. Include the token in the `Authorization` header:

```
Authorization: Bearer <access_token>
```

Tokens are obtained via `POST /api/v1/auth/login` and expire after 30 minutes.

## Dashboard Pages

The React dashboard provides role-based views for analysts, risk engineers, and compliance teams:

- **Overview** — Model health gauge, live transaction flow, confidence/drift/fairness/explainability subscores, governance action feed, and story timeline
- **Review Queue** — Flagged transactions table with filters (date range, confidence threshold), detail panel with SHAP snapshot, and bulk status actions
- **Drift Monitoring** — Statistical drift, concept drift timeline, semantic drift, and distribution comparison charts
- **Explainability** — Global SHAP feature importance and local LIME explanations for individual decisions
- **Fairness Monitoring** — Protected attribute segment analysis and demographic parity metrics
- **Policies** — Governance policy cards with version history and edit flows
- **Audit Log** — Full audit trail with search, filters, and exportable decision records

## How It Works

1. A transaction is sent to `POST /api/v1/predict`, which returns a fraud prediction, confidence score, risk score, decision, and SHAP-based explanations in real time.
2. Every prediction is logged to the database before any further processing happens, so nothing is lost even if a downstream step fails.
3. In the background, drift detectors compare recent transaction patterns against the distribution the model was trained on, surfaced via `GET /api/v1/summary`.
4. A governance policy engine evaluates drift, confidence, and fairness signals against configurable thresholds (`/api/v1/governance`), deciding whether to alert, recommend a retrain, or trigger a safer fallback.
5. The dashboard (`frontend/`) fetches from `/api/v1/dashboard`, `/api/v1/predictions`, `/api/v1/audit`, and `/api/v1/summary` to render a live view of model health, flagged transactions, and governance history for analysts and risk teams.

## Tech Stack

- **Frontend:** React, Vite, Chart.js
- **Backend:** FastAPI, Uvicorn, SQLAlchemy
- **Model:** scikit-learn pipeline with SHAP/LIME explainability
- **Database:** SQLite with Alembic migrations
- **Authentication:** JWT (python-jose)
- **Containerization:** Docker, Docker Compose
- **Testing:** pytest

## License

This project is licensed under the [MIT License](LICENSE).
