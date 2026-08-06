from __future__ import annotations

from typing import Any

import numpy as np

from backend.explainability.feature_importance import FeatureImportanceService


class LimeService:
    def __init__(self, sample_size: int = 256) -> None:
        self.sample_size = sample_size
        self.fallback = FeatureImportanceService()

    def explain(self, model: Any, features: dict[str, Any]) -> dict[str, float]:
        try:
            import lime.lime_tabular  # type: ignore
        except Exception:
            importances = self.fallback.explain(model, [features])
            total = sum(abs(value) for value in importances.values()) or 1.0
            return {key: float(value / total) for key, value in importances.items()}
        if not (hasattr(model, "named_steps") and "vectorizer" in model.named_steps and "model" in model.named_steps):
            return self.fallback.explain(model, [features])
        vectorizer = model.named_steps["vectorizer"]
        estimator = model.named_steps["model"]
        transformed = vectorizer.transform([features]).toarray() if hasattr(vectorizer.transform([features]), "toarray") else vectorizer.transform([features])
        feature_names = list(vectorizer.get_feature_names_out())
        jitter = np.random.default_rng(42).normal(0.0, 0.05, size=(min(self.sample_size, 50), transformed.shape[1]))
        training_data = np.clip(transformed + jitter, a_min=-5.0, a_max=5.0)
        explainer = lime.lime_tabular.LimeTabularExplainer(training_data, feature_names=feature_names, mode="classification")
        explanation = explainer.explain_instance(transformed[0], estimator.predict_proba)
        return {name: float(weight) for name, weight in explanation.as_list()}
