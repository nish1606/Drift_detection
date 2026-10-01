"""LIME must be seeded, non-degenerate, and built on the real background sample."""
from __future__ import annotations

import numpy as np
import pytest

from backend.explainability.background import training_background
from backend.explainability.lime_service import LIME_RANDOM_STATE, LimeService
from backend.explainability.shap_service import ShapService
from ml_model.train import FraudModelTrainer

SAMPLE = {"amount": 5000, "transaction_hour": 22, "country": "NG", "velocity_1h": 7, "geo_distance": 700}


def _dataset(rows: int = 400, seed: int = 42):
    """Large enough that the fitted logistic model does not saturate everywhere."""
    rng = np.random.default_rng(seed)
    features = []
    labels = []
    for _ in range(rows):
        risky = rng.random() < 0.3
        amount = float(rng.gamma(2.0, 1200.0) * (12.0 if risky else 1.0))
        record = {
            "amount": amount,
            "transaction_hour": int(rng.integers(0, 24)),
            "country": "NG" if risky else "US",
            "velocity_1h": float(rng.poisson(6 if risky else 1)),
            "geo_distance": float(abs(rng.normal(800 if risky else 20, 60))),
        }
        features.append(record)
        labels.append(1 if risky else 0)
    return features, labels


@pytest.fixture(scope="module")
def pipeline(tmp_path_factory):
    pytest.importorskip("lime")
    features, labels = _dataset()
    trainer = FraudModelTrainer(artifact_dir=str(tmp_path_factory.mktemp("artifacts")), scale_features=True)
    return trainer.train(model_name="fraud_classifier", model_version="lime", features=features, labels=labels).pipeline


def test_predictions_vary_across_the_background(pipeline):
    """The background sample must actually exercise the decision surface."""
    estimator = pipeline.named_steps["model"]
    matrix = LimeService()._matrix(pipeline, training_background(limit=0))
    assert estimator.predict_proba(matrix).std(axis=0).max() > 0.1


def test_training_persists_a_real_background_sample(pipeline):
    assert training_background(limit=0)


def test_lime_is_reproducible_across_identical_calls(pipeline):
    first = LimeService().explain(pipeline, SAMPLE)
    second = LimeService().explain(pipeline, SAMPLE)
    assert first == second


def test_lime_values_are_non_degenerate(pipeline):
    values = LimeService().explain(pipeline, SAMPLE)
    assert values
    assert max(abs(value) for value in values.values()) > 1e-3, values


def test_lime_labels_are_stable_across_calls(pipeline):
    first = set(LimeService().explain(pipeline, SAMPLE))
    second = set(LimeService().explain(pipeline, SAMPLE))
    assert first == second
    assert first
    # Every label traces back to a vectorizer feature or one of its bins.
    features = set(pipeline.named_steps["vectorizer"].get_feature_names_out())
    assert any(name in features or any(feature in name for feature in features) for name in first)


def test_lime_uses_a_seeded_random_state():
    assert LIME_RANDOM_STATE == 42
    assert LimeService().random_state == LIME_RANDOM_STATE


def test_shap_is_non_degenerate(pipeline):
    pytest.importorskip("shap")
    values = ShapService().explain(pipeline, [SAMPLE])
    assert values
    assert max(abs(value) for value in values.values()) > 1e-3