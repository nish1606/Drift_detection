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
  - [Run the Whole Project](#run-the-whole-project)
- [API Reference](#api-reference)
- [How It Works](#how-it-works)
- [Tech Stack](#tech-stack)
- [Roadmap](#roadmap)
- [Recent Changes](#recent-changes)
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
Transaction → FastAPI /api/predict → Fraud model → Prediction + confidence
                     │
                     ▼
              Decision logged
                     │
       ┌──────────────┼───────────────┐
       ▼              ▼               ▼
   Drift checks   Explainability   Risk scoring
  (/api/drift)                   (/api/governance)
       └──────────────┬───────────────┘
                       ▼
             Governance policy engine
                       │
                       ▼
         Alerts · Fallback · Freeze · Retrain flag
                       │
                       ▼
         Dashboard & audit log (/api/monitoring)
```

The frontend (`frontend/`) is a thin client — it reads from these APIs and renders them; all decisioning logic lives in the backend so it can be reasoned about, tested, and audited independently of the UI.

## Project Layout

```
Drift_detection/
├── backend/
│   ├── app.py               # FastAPI application factory and API wiring
│   ├── api/                 # Routers (predict, drift, governance, monitoring, health)
│   ├── core/                # Config, exceptions, middleware
│   ├── database/            # SQLAlchemy models, CRUD, engine
│   ├── detection/           # Drift detectors
│   ├── explainability/      # SHAP/LIME services
│   ├── governance/          # Policy engine, decision engine, risk scoring
│   ├── logging/             # Logger, decision logger
│   ├── model/               # Predictor, service, registry
│   ├── monitoring/          # Metrics, dashboard, audit
│   ├── preprocessing/       # Feature engineering
│   ├── response/            # Alerting, freeze, retraining, review queue
│   ├── schemas/             # Pydantic request/response models
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

Open the dashboard at:

```
http://127.0.0.1:5173/
```

### Run the Whole Project

Use two terminals:

1. **Backend:** `uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000`
2. **Frontend:** `cd frontend && npm run dev -- --host 127.0.0.1 --port 5173`

### Run with Docker (optional)

```bash
docker-compose up --build
```

## API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/api/predict` | `POST` | Score a transaction and return a fraud prediction with confidence |
| `/api/health` | `GET` | Service health check |
| `/api/monitoring` | `GET` | Aggregated metrics for the dashboard (transaction volume, flagged counts, confidence trend) |
| `/api/governance` | `GET` | Current governance policy evaluations and recent governance actions |
| `/api/drift` | `GET` | Drift detection results (statistical, concept, and semantic drift signals) |

Full interactive documentation is generated automatically by FastAPI at `/docs` once the backend is running.

## How It Works

1. A transaction is sent to `POST /api/predict`, which returns a fraud prediction and confidence score in real time.
2. Every prediction is logged before any further processing happens, so nothing is lost even if a downstream step fails.
3. In the background, drift detectors compare recent transaction patterns against the distribution the model was trained on, surfaced via `GET /api/drift`.
4. A governance policy engine evaluates drift, confidence, and fairness signals against configurable thresholds (`GET /api/governance`), deciding whether to alert, recommend a retrain, or trigger a safer fallback.
5. The dashboard (`frontend/`) polls `/api/monitoring`, `/api/governance`, and `/api/drift` to render a live view of model health, flagged transactions, and governance history for analysts and risk teams.

## Tech Stack

- **Frontend:** React, Vite
- **Backend:** FastAPI, Uvicorn
- **Model training:** scikit-learn (see `ml_model/train.py`)
- **Database migrations:** Alembic
- **Containerization:** Docker, Docker Compose
- **Linting:** oxlint

## License

This project is licensed under the [MIT License](LICENSE).
