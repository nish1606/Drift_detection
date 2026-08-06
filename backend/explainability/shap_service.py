from __future__ import annotations

from typing import Any

from backend.explainability.feature_importance import FeatureImportanceService


class ShapService:
    def __init__(self) -> None:
        self.fallback = FeatureImportanceService()

    def explain(self, model: Any, features: list[dict[str, Any]]) -> dict[str, float]:
        try:
            import shap  # type: ignore
        except Exception:
            importances = self.fallback.explain(model, features)
            total = sum(abs(value) for value in importances.values()) or 1.0
            return {key: float(value / total) for key, value in importances.items()}
        if hasattr(model, "named_steps") and "vectorizer" in model.named_steps and "model" in model.named_steps:
            vectorizer = model.named_steps["vectorizer"]
            estimator = model.named_steps["model"]
            transformed = vectorizer.transform(features)
            explainer = shap.Explainer(estimator, transformed)
            values = explainer(transformed)
            mean_abs = abs(values.values).mean(axis=0)
            feature_names = vectorizer.get_feature_names_out()
            return {name: float(score) for name, score in zip(feature_names, mean_abs, strict=False)}
        return self.fallback.explain(model, features)
