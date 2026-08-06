from __future__ import annotations

from backend.model.train import FraudModelTrainer


def test_training_produces_artifact(tmp_path):
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
    assert artifact.pipeline is not None
    assert artifact.artifact_path.endswith("fraud_classifier_test.joblib")
    assert artifact.metrics["accuracy"] >= 0.0
