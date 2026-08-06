from __future__ import annotations

from backend.model.predict import FraudPredictor
from backend.model.train import FraudModelTrainer


def test_prediction_uses_trained_model(tmp_path):
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
    predictor = FraudPredictor(model_path=artifact.artifact_path)
    result = predictor.predict({"amount": 5000, "transaction_hour": 22, "country": "NG", "velocity_spike": 1})
    assert 0.0 <= result.probability <= 1.0
    assert result.engineered_features["feature_count"] >= 1
