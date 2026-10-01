from __future__ import annotations

from typing import Any

from backend.explainability.feature_importance import FeatureImportanceService
from backend.explainability.background import training_background


class ShapService:
    def __init__(self) -> None:
        self.fallback = FeatureImportanceService()

    def explain(self, model: Any, features: list[dict[str, Any]]) -> dict[str, float]:
        try:
            import shap  # type: ignore
        except Exception:
            raise ImportError("SHAP is not installed; install the optional explainability dependencies")
        if hasattr(model, "named_steps") and "vectorizer" in model.named_steps and "model" in model.named_steps:
            vectorizer = model.named_steps["vectorizer"]
            estimator = model.named_steps["model"]
            background = vectorizer.transform(training_background(limit=0))
            transformed = vectorizer.transform(features)
            if "scaler" in model.named_steps:
                background = model.named_steps["scaler"].transform(background)
                transformed = model.named_steps["scaler"].transform(transformed)
            explainer = shap.LinearExplainer(estimator, background, max_samples=len(background))
            values = explainer(transformed).values[0]
            feature_names = vectorizer.get_feature_names_out()
            return {name: float(score) for name, score in zip(feature_names, values, strict=False)}
        return self.fallback.explain(model, features)
