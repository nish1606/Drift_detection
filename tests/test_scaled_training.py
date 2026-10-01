"""The scaled pipeline is the recommended configuration and must converge."""
from __future__ import annotations

import warnings

import pytest
from sklearn.exceptions import ConvergenceWarning

from ml_model.train import DEFAULT_MAX_ITER, SCALED_MAX_ITER, FraudModelTrainer

FEATURES = [
    {"amount": 10, "transaction_hour": 1, "country": "US", "velocity_1h": 0, "geo_distance": 1},
    {"amount": 9000, "transaction_hour": 23, "country": "NG", "velocity_1h": 9, "geo_distance": 900},
    {"amount": 15, "transaction_hour": 10, "country": "US", "velocity_1h": 1, "geo_distance": 2},
    {"amount": 8000, "transaction_hour": 22, "country": "NG", "velocity_1h": 7, "geo_distance": 800},
    {"amount": 20, "transaction_hour": 9, "country": "US", "velocity_1h": 0, "geo_distance": 3},
    {"amount": 7000, "transaction_hour": 21, "country": "NG", "velocity_1h": 6, "geo_distance": 700},
    {"amount": 18, "transaction_hour": 8, "country": "US", "velocity_1h": 1, "geo_distance": 4},
    {"amount": 6000, "transaction_hour": 20, "country": "NG", "velocity_1h": 5, "geo_distance": 600},
    {"amount": 25, "transaction_hour": 11, "country": "US", "velocity_1h": 0, "geo_distance": 5},
    {"amount": 5000, "transaction_hour": 19, "country": "NG", "velocity_1h": 8, "geo_distance": 500},
]
LABELS = [0, 1, 0, 1, 0, 1, 0, 1, 0, 1]


def test_legacy_default_max_iter_is_unchanged(tmp_path):
    trainer = FraudModelTrainer(artifact_dir=str(tmp_path / "legacy"))
    assert trainer.scale_features is False
    assert trainer.max_iter == DEFAULT_MAX_ITER
    assert trainer._build_pipeline().named_steps["model"].max_iter == DEFAULT_MAX_ITER


def test_scaled_default_max_iter_is_raised(tmp_path):
    trainer = FraudModelTrainer(artifact_dir=str(tmp_path / "scaled"), scale_features=True)
    assert trainer.max_iter == SCALED_MAX_ITER
    assert SCALED_MAX_ITER > DEFAULT_MAX_ITER
    assert trainer._build_pipeline().named_steps["model"].max_iter == SCALED_MAX_ITER


def test_explicit_max_iter_overrides_the_default(tmp_path):
    trainer = FraudModelTrainer(artifact_dir=str(tmp_path / "scaled"), scale_features=True, max_iter=123)
    assert trainer._build_pipeline().named_steps["model"].max_iter == 123


def test_scaled_pipeline_converges_without_warning(tmp_path):
    trainer = FraudModelTrainer(artifact_dir=str(tmp_path / "scaled"), scale_features=True)
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        artifact = trainer.train(model_name="fraud_classifier", model_version="scaled", features=FEATURES, labels=LABELS)
    assert not any(issubclass(item.category, ConvergenceWarning) for item in captured)
    estimator = artifact.pipeline.named_steps["model"]
    assert int(estimator.n_iter_) < int(estimator.max_iter)


def test_model_type_and_split_are_unchanged(tmp_path):
    """The fix must not swap the estimator or alter the split."""
    from sklearn.linear_model import LogisticRegression

    legacy = FraudModelTrainer(artifact_dir=str(tmp_path / "legacy"))._build_pipeline()
    scaled = FraudModelTrainer(artifact_dir=str(tmp_path / "scaled"), scale_features=True)._build_pipeline()
    for pipeline in (legacy, scaled):
        estimator = pipeline.named_steps["model"]
        assert isinstance(estimator, LogisticRegression)
        assert estimator.class_weight == "balanced"
    assert [name for name, _ in legacy.steps] == ["vectorizer", "model"]
    assert [name for name, _ in scaled.steps] == ["vectorizer", "scaler", "model"]