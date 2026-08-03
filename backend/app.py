"""FastAPI service for fraud prediction, decision logging, drift detection, and explanations."""
import os
import time
import uuid
import joblib
import json
from typing import Optional
from fastapi import FastAPI
from pydantic import BaseModel
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
import shap
from river.drift import ADWIN

BASE = os.path.dirname(__file__)
MODEL_PATH = os.path.join(BASE, 'fraud_model.pkl')
SCALER_PATH = os.path.join(BASE, 'scaler.pkl')
TRAIN_STATS = os.path.join(BASE, 'train_stats.npz')
META_PATH = os.path.join(BASE, 'model_meta.pkl')
FEATURE_COLUMNS_PATH = os.path.join(BASE, 'feature_columns.pkl')
LOG_PATH = os.path.join(BASE, 'decision_log.jsonl')

app = FastAPI()


class PredictRequest(BaseModel):
    amount: float
    country: str
    new_device: bool


def load_model():
    model = None
    scaler = None
    meta = {'model_version': 'unknown'}
    feature_columns = ['Amount', 'is_foreign', 'new_device']
    if os.path.exists(MODEL_PATH):
        model = joblib.load(MODEL_PATH)
    if os.path.exists(SCALER_PATH):
        scaler = joblib.load(SCALER_PATH)
    if os.path.exists(META_PATH):
        meta = joblib.load(META_PATH)
    if os.path.exists(FEATURE_COLUMNS_PATH):
        feature_columns = joblib.load(FEATURE_COLUMNS_PATH)
    return model, scaler, meta, feature_columns


model, scaler, meta, feature_columns = load_model()
adwin = ADWIN()


def simple_features(req: PredictRequest):
    is_foreign = 1 if req.country != 'UK' else 0
    new_device = 1 if req.new_device else 0
    feature_values = {
        'Amount': req.amount,
        'amount': req.amount,
        'is_foreign': is_foreign,
        'isForeign': is_foreign,
        'new_device': 1 if req.new_device else 0,
        'newDevice': 1 if req.new_device else 0,
        'country': req.country,
    }
    row = {}
    for column in feature_columns:
        if column in feature_values:
            row[column] = feature_values[column]
        elif column.lower() in feature_values:
            row[column] = feature_values[column.lower()]
        else:
            row[column] = 0.0
    return pd.DataFrame([row], columns=feature_columns)


def compute_psi(expected_probs, expected_bins, actual_values):
    # compute histogram of actual_values using expected_bins
    hist, _ = np.histogram(actual_values, bins=expected_bins)
    actual_probs = hist.astype(float) / hist.sum()
    # replace zeros
    eps = 1e-6
    expected_probs = np.clip(expected_probs, eps, 1)
    actual_probs = np.clip(actual_probs, eps, 1)
    psi = np.sum((expected_probs - actual_probs) * np.log(expected_probs / actual_probs))
    return psi


def log_decision(entry: dict):
    with open(LOG_PATH, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry) + '\n')


@app.post('/predict')
def predict(req: PredictRequest):
    global model, scaler, meta, adwin
    if model is None or scaler is None:
        return {"error": "Model not loaded. Run training first."}

    X = simple_features(req)
    X_scaled = scaler.transform(X)
    proba = float(model.predict_proba(X_scaled)[0, 1])
    pred_label = 'fraud' if proba > 0.5 else 'legit'

    # SHAP explanation
    explainer = shap.TreeExplainer(model)
    shap_vals = explainer.shap_values(X_scaled)
    if isinstance(shap_vals, list):
        shap_vals = shap_vals[1] if len(shap_vals) > 1 else shap_vals[0]
    shap_vals = np.asarray(shap_vals).reshape(-1)
    feature_names = feature_columns
    top_idx = np.argsort(-np.abs(shap_vals))[:3]
    reasons = [feature_names[i] for i in top_idx if abs(shap_vals[i]) > 0]

    # Log decision
    entry = {
        'decision_id': str(uuid.uuid4()),
        'timestamp': time.time(),
        'prediction': pred_label,
        'confidence': proba,
        'model_version': meta.get('model_version', 'unknown'),
        'features': {'amount': req.amount, 'country': req.country, 'new_device': req.new_device}
    }
    log_decision(entry)

    # Update ADWIN for concept drift on label stream
    adwin.update(int(proba > 0.5))
    adwin_warning = bool(getattr(adwin, 'drift_detected', False))

    return {'prediction': pred_label, 'confidence': round(proba, 4), 'reasons': reasons, 'adwin_warning': bool(adwin_warning)}


@app.get('/drift-status')
def drift_status():
    # compute PSI for Amount using saved train stats against last N logged decisions
    if not os.path.exists(TRAIN_STATS):
        return {'drift': False, 'psi': None}

    stats = np.load(TRAIN_STATS, allow_pickle=True)
    bin_edges = stats['bin_edges']
    expected_probs = stats['probs']

    # load recent amounts from log
    if not os.path.exists(LOG_PATH):
        return {'drift': False, 'psi': 0.0}
    amounts = []
    with open(LOG_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                obj = json.loads(line)
                amounts.append(obj['features']['amount'])
            except Exception:
                continue
    if len(amounts) < 10:
        return {'drift': False, 'psi': 0.0}

    psi = compute_psi(expected_probs, bin_edges, np.array(amounts))
    drift = psi > 0.2

    return {'drift': bool(drift), 'psi': float(psi)}


@app.get('/model-health')
def model_health():
    # quick summaries
    size = os.path.getsize(MODEL_PATH) if os.path.exists(MODEL_PATH) else 0
    log_count = 0
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH, 'r', encoding='utf-8') as f:
            log_count = sum(1 for _ in f)
    return {'model_version': meta.get('model_version', 'unknown'), 'model_size_bytes': size, 'decisions_logged': log_count}


@app.get('/alerts')
def alerts():
    ds = drift_status()
    action = 'continue'
    psi = ds.get('psi') or 0
    if psi > 0.25:
        action = 'freeze_model'
    elif psi > 0.15:
        action = 'recommend_retrain'
    return {'psi': psi, 'action': action}


@app.get('/audit-log')
def audit_log(limit: Optional[int] = 100):
    logs = []
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if i >= limit:
                    break
                try:
                    logs.append(json.loads(line))
                except Exception:
                    continue
    return {'logs': logs}
