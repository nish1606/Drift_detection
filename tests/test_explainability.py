from __future__ import annotations

from backend.explainability.lime_service import LimeService
from backend.explainability.shap_service import ShapService
from ml_model.train import FraudModelTrainer


def test_explainability_services_return_mappings(tmp_path):
    trainer = FraudModelTrainer(artifact_dir=str(tmp_path / "artifacts"))
    features = [
        {"amount": 10, "transaction_hour": 1, "country": "US", "velocity_spike": 0},
        {"amount": 9000, "transaction_hour": 23, "country": "NG", "velocity_spike": 1},
        {"amount": 15, "transaction_hour": 10, "country": "US", "velocity_spike": 0},
        {"amount": 8000, "transaction_hour": 22, "country": "NG", "velocity_spike": 1},
        {"amount": 20, "transaction_hour": 9, "country": "US", "velocity_spike": 0},
        {"amount": 7000, "transaction_hour": 21, "country": "NG", "velocity_spike": 1},
        {"amount": 18, "transaction_hour": 8, "country": "US", "velocity_spike": 0},
        {"amount": 6000, "transaction_hour": 20, "country": "NG", "velocity_spike": 1},
    ]
    labels = [0, 1, 0, 1, 0, 1, 0, 1]
    artifact = trainer.train(model_name="fraud_classifier", model_version="test", features=features, labels=labels)
    sample = {"amount": 5000, "transaction_hour": 22, "country": "NG", "velocity_spike": 1}
    shap_result = ShapService().explain(artifact.pipeline, [sample])
    lime_result = LimeService().explain(artifact.pipeline, sample)
    assert isinstance(shap_result, dict)
    assert isinstance(lime_result, dict)
