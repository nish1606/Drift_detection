from __future__ import annotations

import random
from datetime import UTC, datetime
from typing import Any


class LiveTransactionGenerator:
    def __init__(self, baseline_stats: dict[str, dict[str, float]] | None = None, seed: int = 42) -> None:
        self.rng = random.Random(seed)
        self.baseline = baseline_stats or {}
        self.drift_state = {
            "amount_shift": 0.0,
            "velocity_shift": 0.0,
            "geo_shift": 0.0,
            "foreign_boost": 0.0,
            "device_boost": 0.0,
        }

    def _clamp(self, value: float, min_v: float, max_v: float) -> float:
        return max(min_v, min(max_v, value))

    def _sample_normal(self, mean: float, std: float) -> float:
        return self.rng.gauss(mean, std)

    def _sample_positive(self, mean: float, std: float, min_v: float = 0.0) -> float:
        value = self._sample_normal(mean, std)
        return max(min_v, value)

    def apply_drift(self, amount_shift: float = 0.0, velocity_shift: float = 0.0, geo_shift: float = 0.0, foreign_boost: float = 0.0, device_boost: float = 0.0) -> None:
        self.drift_state["amount_shift"] += amount_shift
        self.drift_state["velocity_shift"] += velocity_shift
        self.drift_state["geo_shift"] += geo_shift
        self.drift_state["foreign_boost"] = self._clamp(self.drift_state["foreign_boost"] + foreign_boost, 0.0, 0.9)
        self.drift_state["device_boost"] = self._clamp(self.drift_state["device_boost"] + device_boost, 0.0, 0.9)

    def reset_drift(self) -> None:
        self.drift_state = {
            "amount_shift": 0.0,
            "velocity_shift": 0.0,
            "geo_shift": 0.0,
            "foreign_boost": 0.0,
            "device_boost": 0.0,
        }

    def generate(self, timestamp: datetime | None = None) -> dict[str, Any]:
        ts = timestamp or datetime.now(UTC)
        amount_stats = self.baseline.get("amount", {"mean": 120.0, "std": 180.0, "min": 0.5, "max": 5000.0})
        velocity_stats = self.baseline.get("velocity_1h", {"mean": 1.5, "std": 1.5, "min": 0.0, "max": 20.0})
        geo_stats = self.baseline.get("geo_distance", {"mean": 15.0, "std": 40.0, "min": 0.0, "max": 500.0})
        account_age_stats = self.baseline.get("account_age_days", {"mean": 1825.0, "std": 1500.0, "min": 1.0, "max": 3650.0})
        avg_amount_stats = self.baseline.get("avg_amount_last_30d", {"mean": 100.0, "std": 120.0, "min": 0.0, "max": 3000.0})

        amount = self._sample_positive(amount_stats["mean"] + self.drift_state["amount_shift"], amount_stats["std"], amount_stats["min"])
        amount = min(amount, amount_stats["max"])
        velocity = max(0.0, self._sample_normal(velocity_stats["mean"] + self.drift_state["velocity_shift"], velocity_stats["std"]))
        velocity = min(velocity, velocity_stats["max"])
        geo = max(0.0, self._sample_normal(geo_stats["mean"] + self.drift_state["geo_shift"], geo_stats["std"]))
        geo = min(geo, geo_stats["max"])
        account_age = self._sample_positive(account_age_stats["mean"], account_age_stats["std"], account_age_stats["min"])
        account_age = min(account_age, account_age_stats["max"])
        avg_amount = self._sample_positive(avg_amount_stats["mean"], avg_amount_stats["std"], avg_amount_stats["min"])
        avg_amount = min(avg_amount, avg_amount_stats["max"])

        foreign_prob = self._clamp(0.3 + self.drift_state["foreign_boost"], 0.0, 1.0)
        is_foreign = 1 if self.rng.random() < foreign_prob else 0
        device_prob = self._clamp(0.2 + self.drift_state["device_boost"], 0.0, 1.0)
        new_device = 1 if self.rng.random() < device_prob else 0

        merchant_categories = ["credit", "debit", "grocery", "travel", "digital", "retail"]
        merchant_category = self.rng.choice(merchant_categories)
        transaction_hour = int(self.rng.uniform(0, 23.999))

        return {
            "timestamp": ts.isoformat(),
            "amount": round(amount, 2),
            "transaction_hour": transaction_hour,
            "is_foreign": is_foreign,
            "velocity_1h": round(velocity, 2),
            "new_device": new_device,
            "account_age_days": round(account_age, 1),
            "avg_amount_last_30d": round(avg_amount, 2),
            "merchant_category": merchant_category,
            "geo_distance": round(geo, 2),
        }
