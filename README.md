# Fraud Governance System

This repository combines a React/Vite frontend, a FastAPI backend, and a lightweight fraud-detection model training pipeline. The frontend provides the dashboard experience, the backend exposes prediction, drift, governance, and monitoring APIs, and the training script produces the model artifacts used by the demo.

## Project Layout

- `src/` - React/Vite frontend
- `backend/` - FastAPI app, model training code, and governance modules
- `backend/train.py` - trains the fraud model and writes the model artifacts
- `backend/app.py` - FastAPI application factory and API wiring
- `backend/data/creditcard.csv` - optional training dataset

## Requirements

- Python 3.10+
- Node.js 18+
- `pip`

## Backend Setup

Install the Python dependencies from the repository root:

```bash
pip install -r backend/requirements.txt
```

If you want to use the root project dependencies as well, install them too:

```bash
pip install -r requirements.txt
```

Train the fraud model and generate the saved artifacts:

```bash
python -m backend.train
```

Start the FastAPI backend:

```bash
uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000
```

API docs are available at:

- `http://127.0.0.1:8000/docs`

## Frontend Setup

Install the frontend dependencies:

```bash
npm install
```

Run the Vite app:

```bash
npm run dev -- --host 127.0.0.1 --port 5173
```

Open:

- `http://127.0.0.1:5173/`

## Run The Whole Project

Use two terminals:

1. Start the backend with `uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000`
2. Start the frontend with `npm run dev -- --host 127.0.0.1 --port 5173`

If you update the training data, rerun `python -m backend.train` so the model artifacts stay in sync.

## Main Backend Endpoints

- `POST /api/predict`
- `GET /api/health`
- `GET /api/monitoring`
- `GET /api/governance`
- `GET /api/drift`

## Notes

The demo ships with both the restored frontend and the model artifacts so the full project can be run locally without rebuilding the repository history.
