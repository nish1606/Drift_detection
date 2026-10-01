from __future__ import annotations

from typing import Any

from backend.explainability.background import training_background
from backend.explainability.feature_importance import FeatureImportanceService

#: Seeded so repeated explanations of the same transaction are identical.
LIME_RANDOM_STATE = 42


class LimeService:
    def __init__(self, sample_size: int = 256, num_samples: int = 512, random_state: int = LIME_RANDOM_STATE) -> None:
        self.sample_size = sample_size
        self.num_samples = num_samples
        self.random_state = random_state
        self.fallback = FeatureImportanceService()

    def _matrix(self, model: Any, rows: list[dict[str, Any]]) -> Any:
        vectorizer = model.named_steps["vectorizer"]
        matrix = vectorizer.transform(rows)
        if hasattr(matrix, "toarray"):
            matrix = matrix.toarray()
        if "scaler" in model.named_steps:
            matrix = model.named_steps["scaler"].transform(matrix)
        return matrix

    def explain(self, model: Any, features: dict[str, Any]) -> dict[str, float]:
        try:
            import lime.lime_tabular  # type: ignore
        except Exception:
            raise ImportError("LIME is not installed; install the optional explainability dependencies")
        if not (hasattr(model, "named_steps") and "vectorizer" in model.named_steps and "model" in model.named_steps):
            return self.fallback.explain(model, [features])
        vectorizer = model.named_steps["vectorizer"]
        estimator = model.named_steps["model"]
        # Use the whole persisted background so the local surrogate is fitted on
        # the distribution the model was trained on, not a truncated sample.
        background = self._matrix(model, training_background(limit=0))
        transformed = self._matrix(model, [features])
        feature_names = list(vectorizer.get_feature_names_out())
        explainer = lime.lime_tabular.LimeTabularExplainer(
            background,
            feature_names=feature_names,
            mode="classification",
            # Discretising keeps perturbations inside the observed feature bins.
            # With continuous Gaussian sampling the one-hot and engineered columns
            # are pushed far outside their support, every sample saturates the
            # logistic model and the surrogate returns ~1e-38 for every weight.
            discretize_continuous=True,
            random_state=self.random_state,
        )
        explanation = explainer.explain_instance(
            transformed[0],
            estimator.predict_proba,
            num_samples=self.num_samples,
        )
        return {name: float(weight) for name, weight in explanation.as_list()}