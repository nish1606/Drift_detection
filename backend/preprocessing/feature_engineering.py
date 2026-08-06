from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from backend.preprocessing.clean import clean_features
from backend.preprocessing.encoding import encode_categoricals
from backend.preprocessing.scaling import FeatureScaler


class FeatureEngineer:
    def __init__(self) -> None:
        self.scaler = FeatureScaler()

    def build(self, raw_features: Mapping[str, Any]) -> dict[str, float]:
        cleaned = clean_features(raw_features)
        engineered = encode_categoricals(cleaned)
        numeric_values = {key: float(value) for key, value in engineered.items() if isinstance(value, (int, float))}
        engineered["feature_count"] = float(len(cleaned))
        engineered["numeric_count"] = float(len(numeric_values))
        amount = float(cleaned.get("amount", 0.0))
        engineered["amount_log"] = float(__import__("math").log1p(max(amount, 0.0)))
        transaction_hour = float(cleaned.get("transaction_hour", 0.0))
        engineered["hour_sin"] = float(__import__("math").sin(transaction_hour / 24.0 * 2.0 * __import__("math").pi))
        engineered["hour_cos"] = float(__import__("math").cos(transaction_hour / 24.0 * 2.0 * __import__("math").pi))
        return engineered
