from __future__ import annotations

import threading
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

import joblib
from sqlalchemy.orm import Session

from backend.database import crud
from backend.database.postgres import get_session
from backend.model.predict import FraudPredictor
from backend.streaming.live_generator import LiveTransactionGenerator

BASE_DIR = Path(__file__).resolve().parent.parent
ARTIFACT_DIR = BASE_DIR / "ml_model" / "artifacts"
BASELINE_STATS_PATH = ARTIFACT_DIR / "baseline_stats.pkl"


class LiveTransactionStream:
    def __init__(self, interval_seconds: int = 15, batch_size: int = 3, predictor: FraudPredictor | None = None) -> None:
        self.interval_seconds = interval_seconds
        self.batch_size = batch_size
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._drift_injected = False
        self.predictor = predictor

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=5)

    def _load_baseline(self) -> dict[str, dict[str, float]] | None:
        if BASELINE_STATS_PATH.exists():
            try:
                return joblib.load(BASELINE_STATS_PATH)
            except Exception:
                return None
        return None

    def _run(self) -> None:
        baseline = self._load_baseline()
        generator = LiveTransactionGenerator(baseline_stats=baseline, seed=42)
        tick = 0
        while not self._stop.is_set():
            try:
                db = get_session()
                try:
                    if tick == 20 and not self._drift_injected:
                        generator.apply_drift(amount_shift=300.0, velocity_shift=3.0, geo_shift=80.0, foreign_boost=0.4, device_boost=0.5)
                        self._drift_injected = True
                    self._insert_batch(db, generator)
                    db.commit()
                finally:
                    db.close()
            except Exception:
                pass
            tick += 1
            self._stop.wait(self.interval_seconds)

    def _insert_batch(self, db: Session, generator: LiveTransactionGenerator) -> None:
        now = datetime.now(UTC)
        payloads = []
        for idx in range(self.batch_size):
            raw = generator.generate(timestamp=now - timedelta(seconds=idx * 5))
            amount = float(raw["amount"])
            velocity = float(raw["velocity_1h"])
            geo = float(raw["geo_distance"])
            foreign = int(raw["is_foreign"])
            new_device_flag = int(raw["new_device"])
            account_age = float(raw["account_age_days"])

            if self.predictor is not None:
                result = self.predictor.predict(raw)
                score = float(result.probability)
                prediction = int(result.prediction)
                decision = result.decision
                top_features = result.explanations.get("top_features", [])
            else:
                score = min(1.0, max(0.0, 0.25 + 0.0004 * amount + 0.18 * velocity + 0.25 * geo / 100 + 0.45 * foreign + 0.35 * new_device_flag - 0.003 * account_age))
                prediction = 1 if score >= 0.5 else 0
                if score >= 0.75:
                    decision = "block"
                elif score >= 0.45:
                    decision = "review"
                else:
                    decision = "approve"
                contributions = {
                    "amount": 0.0004 * amount,
                    "velocity_1h": 0.18 * velocity,
                    "geo_distance": 0.25 * geo / 100,
                    "is_foreign": 0.45 * foreign,
                    "new_device": 0.35 * new_device_flag,
                    "account_age_days": -0.003 * account_age,
                }
                top_features = sorted(
                    [(feature, round(value, 4)) for feature, value in contributions.items()],
                    key=lambda item: abs(item[1]),
                    reverse=True,
                )

            payloads.append({
                "request_id": uuid.uuid4().hex,
                "model_name": "fraud_classifier",
                "model_version": "v4.8.2",
                "raw_features": {
                    "timestamp": raw["timestamp"],
                    "amount": amount,
                    "transaction_hour": int(raw["transaction_hour"]),
                    "is_foreign": foreign,
                    "velocity_1h": velocity,
                    "new_device": new_device_flag,
                    "account_age_days": account_age,
                    "avg_amount_last_30d": float(raw["avg_amount_last_30d"]),
                    "merchant_category": raw["merchant_category"],
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
                    "night_txn": 1.0 if int(raw["transaction_hour"]) < 6 else 0.0,
                },
                "prediction": prediction,
                "probability": round(score, 4),
                "risk_score": round(min(1.0, score + 0.15 * float(velocity > 3)), 4),
                "decision": decision,
                "explanations": {
                    "top_features": top_features,
                    "fallback": self.predictor is None or self.predictor.model is None,
                },
                "created_at": datetime.now(UTC),
            })

        crud.bulk_create_prediction_records(db, payloads)
        self._update_drift_metrics(db, now, generator)

    def _update_drift_metrics(self, db: Session, now: datetime, generator: LiveTransactionGenerator) -> None:
        recent = crud.list_predictions(db, limit=100)
        if not recent:
            return
        amounts = [float(r.raw_features.get("amount", 0)) for r in recent if isinstance(r.raw_features, dict)]
        velocities = [float(r.raw_features.get("velocity_1h", 0)) for r in recent if isinstance(r.raw_features, dict)]
        geos = [float(r.raw_features.get("geo_distance", 0)) for r in recent if isinstance(r.raw_features, dict)]

        def _metric_value(values: list[float], baseline_mean: float, baseline_std: float) -> float:
            if not values or baseline_std <= 0:
                return 0.0
            live_mean = sum(values) / len(values)
            live_std = (sum((x - live_mean) ** 2 for x in values) / len(values)) ** 0.5
            mean_diff = abs(live_mean - baseline_mean) / (baseline_std + 1e-6)
            std_ratio = live_std / (baseline_std + 1e-6)
            return round(min(0.3, max(0.02, mean_diff * 0.1 + std_ratio * 0.05)), 4)

        baseline = generator.baseline or {}
        for feature, values, baseline_key in [
            ("transactionAmount", amounts, "amount"),
            ("deviceVelocity", velocities, "velocity_1h"),
            ("geoDistance", geos, "geo_distance"),
        ]:
            b = baseline.get(baseline_key, {})
            crud.create_drift_metric(db, {
                "detector_name": "statistical_drift",
                "feature_name": feature,
                "metric_value": _metric_value(values, b.get("mean", 0.0), b.get("std", 1.0)),
                "threshold": 0.2,
                "status": "Alert",
                "details": {},
                "created_at": now,
            })
