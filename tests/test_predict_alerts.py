"""/predict must return the alerts it raises instead of a hard-coded empty list."""
from __future__ import annotations

from unittest.mock import patch

import numpy as np
import pytest
from fastapi.testclient import TestClient

from ml_model.train import FraudModelTrainer


@pytest.fixture()
def api(app, settings):
    rng = np.random.default_rng(11)
    features, labels = [], []
    for _ in range(300):
        risky = rng.random() < 0.3
        features.append(
            {
                "amount": float(rng.gamma(2, 1200) * (12 if risky else 1)),
                "transaction_hour": int(rng.integers(0, 24)),
                "country": "NG" if risky else "US",
                "velocity_1h": float(rng.poisson(6 if risky else 1)),
                "geo_distance": float(abs(rng.normal(800 if risky else 20, 60))),
            }
        )
        labels.append(1 if risky else 0)
    FraudModelTrainer(artifact_dir=settings.model_store_path, scale_features=True).train(
        model_name="fraud_classifier", model_version="alerts", features=features, labels=labels
    )
    with TestClient(app) as client:
        login = client.post("/api/v1/auth/login", data={"username": "analyst", "password": "analyst123"})
        client.headers.update({"Authorization": f"Bearer {login.json()['access_token']}"})
        yield client


RISKY = {"amount": 9000, "transaction_hour": 23, "country": "NG", "velocity_1h": 9, "geo_distance": 900}
BENIGN = {"amount": 12, "transaction_hour": 10, "country": "US", "velocity_1h": 0, "geo_distance": 2}


def _post(client, features):
    response = client.post("/api/v1/predict", json={"features": features})
    assert response.status_code == 200, response.text
    return response.json()


def test_blocked_decision_returns_an_alert(api):
    payload = _post(api, RISKY)
    assert payload["decision"] in {"block", "freeze", "review"}
    assert payload["alerts"], payload
    alert = payload["alerts"][0]
    assert alert["id"] is not None
    assert alert["severity"] == "high" if payload["decision"] in {"block", "freeze"} else alert["severity"] == "medium"
    assert payload["decision"] in alert["message"]


def test_allowed_decision_returns_no_alerts(api):
    payload = _post(api, BENIGN)
    if payload["decision"] == "allow":
        assert payload["alerts"] == []
    else:
        assert payload["alerts"]


def test_alert_is_persisted_and_matches_the_response(api):
    payload = _post(api, RISKY)
    if not payload["alerts"]:
        pytest.skip("model did not produce an actionable decision")
    alert_id = payload["alerts"][0]["id"]
    from backend.database.postgres import get_session

    session = get_session()
    try:
        stored = session.get(__import__("backend.database.models", fromlist=["Alert"]).Alert, alert_id)
        assert stored is not None
        assert stored.message == payload["alerts"][0]["message"]
        assert stored.is_resolved is False
    finally:
        session.close()


def test_alerting_is_not_silently_dropped(api):
    """The alert must be created in the request path, not only in the background task."""
    with patch("backend.api.predict.AlertingService") as service:
        service.return_value.create_alert.side_effect = RuntimeError("boom")
        with pytest.raises(RuntimeError):
            api.post("/api/v1/predict", json={"features": RISKY})
    assert service.called, "AlertingService was never invoked on the request path"