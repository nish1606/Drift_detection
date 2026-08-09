import json
import random
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from backend.core.auth import get_password_hash
from backend.core.config import get_settings
from backend.database import crud
from backend.database.models import User
from backend.database.postgres import configure_engine, get_session

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUT_CSV = DATA_DIR / "transactions_realistic.csv"
SCHEMA_PATH = DATA_DIR / "transactions_realistic_schema.json"
SEED_USERS = [
    {"username": "analyst", "password": "analyst123", "role": "Analyst", "display_name": "Analyst User"},
    {"username": "risk_engineer", "password": "risk123", "role": "RiskEngineer", "display_name": "Risk Engineer"},
    {"username": "compliance", "password": "compliance123", "role": "Compliance", "display_name": "Compliance User"},
]


def _generate_dataset(n_rows: int = 5000) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    timestamps = [datetime.now(UTC) - timedelta(minutes=random.randint(0, 60 * 24 * 30)) for _ in range(n_rows)]
    timestamps.sort()

    merchant_categories = random.choices(["credit", "debit", "grocery", "travel", "digital", "retail"], weights=[20, 20, 15, 10, 15, 20], k=n_rows)
    amounts = np.abs(rng.normal(120, 180, n_rows)).clip(0.5, 5000)
    transaction_hours = [int(t.hour + t.minute / 60) for t in timestamps]
    is_foreign = rng.integers(0, 2, n_rows).tolist()
    velocity_1h = rng.exponential(1.5, n_rows).clip(0, 20).tolist()
    new_device = rng.integers(0, 2, n_rows).tolist()
    account_age_days = rng.integers(1, 3650, n_rows).tolist()
    avg_amount_last_30d = np.abs(rng.normal(100, 120, n_rows)).clip(0, 3000).tolist()
    geo_distance = np.abs(rng.normal(15, 40, n_rows)).clip(0, 500).tolist()

    logits = (
        -3.2
        + 0.0004 * amounts
        + 0.18 * np.array(velocity_1h)
        + 0.25 * np.array(geo_distance) / 100
        + 0.45 * np.array(is_foreign)
        + 0.35 * np.array(new_device)
        - 0.003 * np.array(account_age_days)
        + rng.normal(0, 1.2, n_rows)
    )
    probs = 1 / (1 + np.exp(-logits))
    is_fraud = rng.random(n_rows) < probs

    df = pd.DataFrame({
        "timestamp": [t.isoformat() for t in timestamps],
        "amount": np.round(amounts, 2).tolist(),
        "transaction_hour": transaction_hours,
        "is_foreign": is_foreign,
        "velocity_1h": np.round(velocity_1h, 2).tolist(),
        "new_device": new_device,
        "account_age_days": account_age_days,
        "avg_amount_last_30d": np.round(avg_amount_last_30d, 2).tolist(),
        "merchant_category": merchant_categories,
        "geo_distance": np.round(geo_distance, 2).tolist(),
        "isFraud": is_fraud.astype(int).tolist(),
    })
    return df


def generate_schema(df: pd.DataFrame, target: str = "isFraud") -> dict:
    numeric_cols = df.select_dtypes(include=["number"]).columns.drop(target, errors="ignore").tolist()
    categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    boolean_cols = [c for c in df.columns if c not in numeric_cols + categorical_cols + [target]]
    return {
        "columns": df.columns.drop(target).tolist() if target in df.columns else df.columns.tolist(),
        "target": target,
        "categorical": categorical_cols,
        "numeric": numeric_cols,
        "boolean": boolean_cols,
    }


def _build_prediction(row: pd.Series, idx: int, model_version: str = "v4.8.2") -> dict:
    amount = float(row["amount"])
    velocity = float(row["velocity_1h"])
    geo = float(row["geo_distance"])
    foreign = int(row["is_foreign"])
    new_device_flag = int(row["new_device"])
    account_age = float(row["account_age_days"])
    created_at = datetime.fromisoformat(row["timestamp"])

    score = min(1.0, max(0.0, 0.25 + 0.0004 * amount + 0.18 * velocity + 0.25 * geo / 100 + 0.45 * foreign + 0.35 * new_device_flag - 0.003 * account_age))
    score = max(0.0, min(1.0, score + random.uniform(-0.05, 0.05)))
    prediction = 1 if score >= 0.5 else 0

    if score >= 0.75:
        decision = "block"
    elif score >= 0.45:
        decision = "review"
    else:
        decision = "approve"

    return {
        "request_id": str(uuid.uuid4()),
        "model_name": "fraud_classifier",
        "model_version": model_version,
        "raw_features": {
            "timestamp": row["timestamp"],
            "amount": amount,
            "transaction_hour": int(row["transaction_hour"]),
            "is_foreign": foreign,
            "velocity_1h": velocity,
            "new_device": new_device_flag,
            "account_age_days": account_age,
            "avg_amount_last_30d": float(row["avg_amount_last_30d"]),
            "merchant_category": row["merchant_category"],
            "geo_distance": geo,
        },
        "engineered_features": {
            "amount": amount,
            "velocity_1h": velocity,
            "account_age_days": account_age,
            "geo_distance": geo,
            "is_foreign": foreign,
            "new_device": new_device_flag,
            "velocity_spike": 1.0 if velocity > 3 else 0.0,
            "high_value": 1.0 if amount > 500 else 0.0,
            "night_txn": 1.0 if int(row["transaction_hour"]) < 6 else 0.0,
        },
        "prediction": prediction,
        "probability": round(score, 4),
        "risk_score": round(min(1.0, score + 0.15 * (velocity > 3)), 4),
        "decision": decision,
        "explanations": {
            "top_features": [
                ["velocity_1h", velocity],
                ["geo_distance", geo],
                ["amount", amount],
                ["is_foreign", foreign],
                ["new_device", new_device_flag],
            ],
            "fallback": True,
        },
        "created_at": created_at,
    }


def _build_drift_metrics(df: pd.DataFrame) -> list[dict]:
    now = datetime.now(UTC)
    metrics = []
    feature_names = ["transactionAmount", "deviceVelocity", "geoDistance"]
    feature_values = {
        "transactionAmount": df["amount"].clip(upper=1000).tolist(),
        "deviceVelocity": df["velocity_1h"].tolist(),
        "geoDistance": df["geo_distance"].clip(upper=200).tolist(),
    }
    for feature in feature_names:
        values = feature_values[feature]
        for i in range(24):
            ts = now - timedelta(hours=23 - i)
            sample = random.sample(values, min(50, len(values)))
            mean = sum(sample) / len(sample)
            std = (sum((x - mean) ** 2 for x in sample) / len(sample)) ** 0.5
            metric_value = min(0.35, max(0.01, std / (mean + 1e-6) + random.uniform(-0.01, 0.02)))
            if metric_value >= 0.2:
                status = "Alert"
            elif metric_value >= 0.14:
                status = "Watch"
            else:
                status = "Normal"
            metrics.append({
                "detector_name": "statistical_drift",
                "feature_name": feature,
                "metric_value": round(float(metric_value), 4),
                "threshold": 0.2,
                "status": status,
                "details": {
                    "mean": round(mean, 3),
                    "std": round(std, 4),
                },
                "created_at": ts,
            })
    return metrics


def _build_audit_logs(df: pd.DataFrame) -> list[dict]:
    now = datetime.now(UTC)
    logs = []
    for i in range(min(20, len(df))):
        row = df.iloc[i]
        score = min(1.0, max(0.0, 0.25 + 0.0004 * float(row["amount"]) + 0.18 * float(row["velocity_1h"]) + 0.25 * float(row["geo_distance"]) / 100))
        if score >= 0.75:
            status = "block"
        elif score >= 0.45:
            status = "review"
        else:
            status = "approve"
        logs.append({
            "actor": "System",
            "action": "predict",
            "resource_type": "transaction",
            "resource_id": str(uuid.uuid4()),
            "status": status,
            "payload": {
                "amount": float(row["amount"]),
                "merchant_category": row["merchant_category"],
                "reason": f"Rule-based score {score:.2f}",
                "probability": round(score, 4),
                "prediction": 1 if score >= 0.5 else 0,
                "model_version": "v4.8.2",
                "features": {
                    "amount": float(row["amount"]),
                    "transaction_hour": int(row["transaction_hour"]),
                    "is_foreign": int(row["is_foreign"]),
                    "velocity_1h": float(row["velocity_1h"]),
                    "new_device": int(row["new_device"]),
                    "account_age_days": float(row["account_age_days"]),
                    "avg_amount_last_30d": float(row["avg_amount_last_30d"]),
                    "merchant_category": row["merchant_category"],
                    "geo_distance": float(row["geo_distance"]),
                },
                "engineered_features": {
                    "amount": float(row["amount"]),
                    "velocity_1h": float(row["velocity_1h"]),
                    "account_age_days": float(row["account_age_days"]),
                    "geo_distance": float(row["geo_distance"]),
                    "is_foreign": int(row["is_foreign"]),
                    "new_device": int(row["new_device"]),
                    "velocity_spike": 1.0 if float(row["velocity_1h"]) > 3 else 0.0,
                    "high_value": 1.0 if float(row["amount"]) > 500 else 0.0,
                    "night_txn": 1.0 if int(row["transaction_hour"]) < 6 else 0.0,
                },
            },
            "created_at": (now - timedelta(minutes=random.randint(0, 60 * 24 * 30))),
        })
    return logs


def seed_users(session: Session):
    for u in SEED_USERS:
        if not session.query(User).filter(User.username == u["username"]).first():
            session.add(User(username=u["username"], display_name=u["display_name"], password_hash=get_password_hash(u["password"]), role=u["role"]))
    session.commit()


def main():
    configure_engine(get_settings().database_url)
    db = get_session()
    try:
        print("Seeding users...")
        seed_users(db)
        print("Seeding users done.")

        print("Generating dataset...")
        df = _generate_dataset(5000)
        df.to_csv(OUT_CSV, index=False)
        print(f"Saved {len(df)} rows to {OUT_CSV}")

        schema = generate_schema(df)
        SCHEMA_PATH.write_text(json.dumps(schema, indent=2))
        print(f"Saved schema to {SCHEMA_PATH}")

        print("Inserting predictions...")
        payloads = [_build_prediction(df.iloc[i], i) for i in range(len(df))]
        crud.bulk_create_prediction_records(db, payloads)
        print(f"Inserted {len(payloads)} predictions.")

        print("Inserting drift metrics...")
        drift_payloads = _build_drift_metrics(df)
        for payload in drift_payloads:
            crud.create_drift_metric(db, payload)
        print(f"Inserted {len(drift_payloads)} drift metrics.")

        print("Inserting audit logs...")
        audit_payloads = _build_audit_logs(df)
        for payload in audit_payloads:
            crud.create_audit_log(db, payload)
        print(f"Inserted {len(audit_payloads)} audit logs.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
