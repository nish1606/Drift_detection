# Drift Detection Demo

This project combines a React/Vite dashboard with a FastAPI fraud-detection backend. The demo includes a trained fraud model, prediction logging, drift detection (PSI + ADWIN), SHAP-style reasons, and governance endpoints for dashboard use.

## What is included

- React + Vite frontend for the governance dashboard
- FastAPI backend for fraud predictions and monitoring
- XGBoost-based fraud model trained from a local CSV sample
- Decision logging for auditability
- Drift detection and alert endpoints
- SHAP-style feature reasons for flagged transactions

## Project structure

- [src](src) — frontend React app
- [backend](backend) — FastAPI app and training pipeline
- [backend/data/creditcard.csv](backend/data/creditcard.csv) — demo training data
- [backend/train.py](backend/train.py) — model training script
- [backend/app.py](backend/app.py) — prediction and monitoring API

## Prerequisites

- Node.js 18+
- Python 3.10+
- pip

## Frontend setup

Install dependencies:

```bash
npm install
```

Run the frontend:

```bash
npm run dev -- --host 127.0.0.1 --port 5173
```

Open http://127.0.0.1:5173/ in your browser.

## Backend setup

From the backend folder:

```bash
cd backend
pip install -r requirements.txt
```

Train the model:

```bash
python train.py
```

Run the API:

```bash
uvicorn app:app --reload --port 8000 --app-dir backend
```

The API will be available at:

- http://127.0.0.1:8000/docs
- POST /predict
- GET /drift-status
- GET /model-health
- GET /alerts
- GET /audit-log

## Example prediction

```bash
curl -X POST http://127.0.0.1:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"amount":45000,"country":"UK","new_device":true}'
```

## Notes

The training data included here is a small synthetic CSV for demo purposes. The backend now infers its feature columns from the CSV automatically, so adding more columns or a richer dataset will be picked up on retraining. If you later add a real Kaggle Credit Card Fraud dataset, place it at [backend/data/creditcard.csv](backend/data/creditcard.csv) and rerun [backend/train.py](backend/train.py).
