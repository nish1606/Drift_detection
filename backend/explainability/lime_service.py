from __future__ import annotations

from typing import Any

import numpy as np

from backend.explainability.feature_importance import FeatureImportanceService
from backend.explainability.background import training_background


class LimeService:
    def __init__(self, sample_size: int = 256) -> None:
        self.sample_size = sample_size
        self.fallback = FeatureImportanceService()

    def explain(self, model: Any, features: dict[str, Any]) -> dict[str, float]:
        try:
            import lime.lime_tabular  # type: ignore
        except Exception:
            raise ImportError("LIME is not installed; install the optional explainability dependencies")
        if not (hasattr(model, "named_steps") and "vectorizer" in model.named_steps and "model" in model.named_steps):
            return self.fallback.explain(model, [features])
        vectorizer = model.named_steps["vectorizer"]
        estimator = model.named_steps["model"]
        background = vectorizer.transform(training_background())
        transformed = vectorizer.transform([features])
        if hasattr(background, "toarray"):
            background = background.toarray()
        if hasattr(transformed, "toarray"):
            transformed = transformed.toarray()
        if "scaler" in model.named_steps:
            background = model.named_steps["scaler"].transform(background)
            transformed = model.named_steps["scaler"].transform(transformed)
        feature_names = list(vectorizer.get_feature_names_out())
        training_data = background
        explainer = lime.lime_tabular.LimeTabularExplainer(training_data, feature_names=feature_names, mode="classification", discretize_continuous=False)
        explanation = explainer.explain_instance(transformed[0], estimator.predict_proba)
        return {name: float(weight) for name, weight in explanation.as_list()}
