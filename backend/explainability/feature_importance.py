from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.inspection import permutation_importance


class FeatureImportanceService:
    def explain(self, model: Any, features: list[dict[str, Any]], labels: list[int] | None = None) -> dict[str, float]:
        if hasattr(model, "named_steps") and "vectorizer" in model.named_steps and "model" in model.named_steps:
            vectorizer = model.named_steps["vectorizer"]
            estimator = model.named_steps["model"]
            feature_names = vectorizer.get_feature_names_out()
            if hasattr(estimator, "coef_"):
                weights = np.asarray(estimator.coef_).reshape(-1)
                return {name: float(abs(weight)) for name, weight in zip(feature_names, weights, strict=False)}
            if hasattr(estimator, "feature_importances_"):
                importances = np.asarray(estimator.feature_importances_)
                return {name: float(value) for name, value in zip(feature_names, importances, strict=False)}
        if labels is not None and hasattr(model, "predict"):
            result = permutation_importance(model, features, labels, n_repeats=5, random_state=42)
            return {f"feature_{index}": float(score) for index, score in enumerate(result.importances_mean)}
        return {}
