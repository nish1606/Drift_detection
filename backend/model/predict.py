from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
from sklearn.pipeline import Pipeline

from backend.core.exceptions import ModelUnavailableError
from backend.model.fallback_rules import rule_based_decision, rule_based_probability
from backend.preprocessing.feature_engineering import FeatureEngineer


@dataclass
class PredictionResult:
    prediction: int
    probability: float
    decision: str
    explanations: dict[str, Any]
    engineered_features: dict[str, Any]
    model_version: str
    model_name: str
    risk_score: float


class FraudPredictor:
    def __init__(self, model: Pipeline | None = None, model_path: str | None = None, model_name: str = "fraud_classifier", model_version: str = "1.0.0") -> None:
        self.feature_engineer = FeatureEngineer()
        self.model = model
        self.model_path = model_path
        self.model_name = model_name
        self.model_version = model_version

    def load(self) -> Pipeline | None:
        if self.model is not None:
            return self.model
        if self.model_path is None:
            return None
        path = Path(self.model_path)
        if not path.exists():
            raise ModelUnavailableError(f"model artifact not found at {path}")
        self.model = joblib.load(path)
        return self.model

    def predict(self, features: dict[str, Any]) -> PredictionResult:
        engineered = self.feature_engineer.build(features)
        model = self.load()
        if model is None:
            probability = rule_based_probability(engineered)
        else:
            probability = float(model.predict_proba([engineered])[0][1])
        prediction = int(probability >= 0.5)
        risk_score = float(min(1.0, probability + 0.15 * engineered.get("velocity_spike", 0.0)))
        decision = rule_based_decision(probability, risk_score)
        explanations = {
            "top_features": sorted(engineered.items(), key=lambda item: abs(float(item[1])), reverse=True)[:8],
            "fallback": model is None,
        }
        return PredictionResult(
            prediction=prediction,
            probability=probability,
            decision=decision,
            explanations=explanations,
            engineered_features=engineered,
            model_version=self.model_version,
            model_name=self.model_name,
            risk_score=risk_score,
        )
