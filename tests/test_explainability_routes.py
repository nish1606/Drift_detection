"""The GET explainability routes must work instead of returning 422."""
from __future__ import annotations

import json

import numpy as np
import pytest

from ml_model.train import FraudModelTrainer

FEATURES = {"amount": 5000, "transaction_hour": 22, "country": "NG", "velocity_1h": 7, "geo_distance": 700}


def _train(store: str) -> None:
    rng = np.random.default_rng(7)
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
    FraudModelTrainer(artifact_dir=store, scale_features=True).train(
        model_name="fraud_classifier", model_version="api", features=features, labels=labels
    )


@pytest.fixture()
def api(app, settings):
    pytest.importorskip("lime")
    _train(settings.model_store_path)
    from fastapi.testclient import TestClient

    with TestClient(app) as test_client:
        login = test_client.post("/api/v1/auth/login", data={"username": "analyst", "password": "analyst123"})
        assert login.status_code == 200
        token = login.json()["access_token"]
        test_client.headers.update({"Authorization": f"Bearer {token}"})
        yield test_client


SHAP_LIME = ["/api/v1/explainability/shap", "/api/v1/explainability/lime"]


@pytest.mark.parametrize("path", SHAP_LIME)
def test_get_explainability_returns_200(api, path):
    response = api.get(path, params={"features": json.dumps(FEATURES)})
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["method"] == path.rsplit("/", 1)[1]
    assert payload["values"]


@pytest.mark.parametrize("path", SHAP_LIME)
def test_get_explainability_requires_the_features_parameter(api, path):
    assert api.get(path).status_code == 422


@pytest.mark.parametrize("path", SHAP_LIME)
def test_get_explainability_rejects_malformed_features(api, path):
    assert api.get(path, params={"features": "not-json"}).status_code == 422
    assert api.get(path, params={"features": json.dumps([1, 2, 3])}).status_code == 422


@pytest.mark.parametrize("path", SHAP_LIME)
def test_get_explainability_rejects_anonymous_callers(api, path):
    assert api.get(path, params={"features": json.dumps(FEATURES)}, headers={"Authorization": ""}).status_code in (401, 403)


def test_get_lime_is_deterministic(api):
    params = {"features": json.dumps(FEATURES)}
    assert api.get("/api/v1/explainability/lime", params=params).json() == api.get(
        "/api/v1/explainability/lime", params=params
    ).json()


def test_shap_and_lime_expose_distinct_operation_ids(api):
    paths = api.get("/openapi.json").json()["paths"]
    for path in SHAP_LIME:
        assert "get" in paths[path]
        assert "post" in paths[path]
    operation_ids = [
        operation["operationId"] for path in paths.values() for operation in path.values() if isinstance(operation, dict)
    ]
    assert len(operation_ids) == len(set(operation_ids))