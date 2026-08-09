import random
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pandas as pd
from sqlalchemy.orm import Session

from backend.core.auth import get_password_hash
from backend.core.config import get_settings
from backend.database import crud
from backend.database.models import User
from backend.database.postgres import configure_engine, get_session

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CSV_PATH = DATA_DIR / "transactions_realistic.csv"
SCHEMA_PATH = DATA_DIR / "transactions_realistic_schema.json"
SEED_USERS = [
    {"username": "analyst", "password": "analyst123", "role": "Analyst", "display_name": "Analyst User"},
    {"username": "risk_engineer", "password": "risk123", "role": "RiskEngineer", "display_name": "Risk Engineer"},
    {"username": "compliance", "password": "compliance123", "role": "Compliance", "display_name": "Compliance User"},
]


def _build_prediction(row: pd.Series, idx: int, model_version: str = "v4.8.2") -> dict:
    amount = float(row["amount"])
    velocity = float(row["velocity_1h"]) if pd.notna(row["velocity_1h"]) else 0.0
    geo = float(row["geo_distance"]) if pd.notna(row["geo_distance"]) else 0.0
    foreign = int(row["is_foreign"]) if pd.notna(row["is_foreign"]) else 0
    new_device_flag = int(row["new_device"]) if pd.notna(row["new_device"]) else 0
    account_age = float(row["account_age_days"]) if pd.notna(row["account_age_days"]) else 0.0
    created_at = datetime.now(UTC) - timedelta(minutes=int(idx / 10))

    score = min(1.0, max(0.0, 0.25 + 0.0004 * amount + 0.18 * velocity + 0.25 * geo / 100 + 0.45 * foreign + 0.35 * new_device_flag - 0.003 * account_age))
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
            "timestamp": created_at.isoformat(),
            "amount": amount,
            "transaction_hour": int(row["transaction_hour"]) if pd.notna(row["transaction_hour"]) else 0,
            "is_foreign": foreign,
            "velocity_1h": velocity,
            "new_device": new_device_flag,
            "account_age_days": account_age,
            "avg_amount_last_30d": float(row["avg_amount_last_30d"]) if pd.notna(row["avg_amount_last_30d"]) else 0.0,
            "merchant_category": row["merchant_category"] if pd.notna(row["merchant_category"]) else "unknown",
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
        "deviceVelocity": df["velocity_1h"].fillna(0).tolist(),
        "geoDistance": df["geo_distance"].fillna(0).tolist(),
    }
    rng = random.Random(42)
    for feature in feature_names:
        values = feature_values[feature]
        for i in range(24):
            ts = now - timedelta(hours=23 - i)
            sample = values[:50] if len(values) >= 50 else values
            mean = sum(sample) / len(sample)
            std = (sum((x - mean) ** 2 for x in sample) / len(sample)) ** 0.5
            cv = std / (mean + 1e-6)
            base = min(0.3, max(0.02, cv * 0.05 + rng.uniform(-0.01, 0.01)))
            metric_value = round(base, 4)
            if metric_value >= 0.2:
                status = "Alert"
            elif metric_value >= 0.14:
                status = "Watch"
            else:
                status = "Normal"
            metrics.append({
                "detector_name": "statistical_drift",
                "feature_name": feature,
                "metric_value": metric_value,
                "threshold": 0.2,
                "status": status,
                "details": {"mean": round(mean, 3), "std": round(std, 4)},
                "created_at": ts,
            })
    return metrics


def _build_audit_logs(df: pd.DataFrame) -> list[dict]:
    now = datetime.now(UTC)
    logs = []
    for i in range(min(20, len(df))):
        row = df.iloc[i]
        amount = float(row["amount"]) if pd.notna(row["amount"]) else 0.0
        velocity = float(row["velocity_1h"]) if pd.notna(row["velocity_1h"]) else 0.0
        geo = float(row["geo_distance"]) if pd.notna(row["geo_distance"]) else 0.0
        foreign = int(row["is_foreign"]) if pd.notna(row["is_foreign"]) else 0
        score = min(1.0, max(0.0, 0.25 + 0.0004 * amount + 0.18 * velocity + 0.25 * geo / 100 + 0.45 * foreign))
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
                "amount": amount,
                "merchant_category": row["merchant_category"] if pd.notna(row["merchant_category"]) else "unknown",
                "reason": f"Rule-based score {score:.2f}",
            },
            "created_at": now - timedelta(minutes=i),
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

        if not CSV_PATH.exists():
            raise FileNotFoundError(f"CSV not found at {CSV_PATH}")

        print(f"Reading real dataset from {CSV_PATH}...")
        df = pd.read_csv(CSV_PATH)
        print(f"Read {len(df)} rows.")

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
