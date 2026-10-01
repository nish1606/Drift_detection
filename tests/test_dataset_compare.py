"""/datasets/compare must support multi-feature and all-feature comparison."""
from __future__ import annotations

import csv
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.detection.dataset_comparison import DATA_DIR

NUMERIC = ["amount", "velocity", "distance"]
CATEGORICAL = ["country"]


def _write(name: str, rows: list[dict[str, object]]) -> str:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / name
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=[*NUMERIC, *CATEGORICAL])
        writer.writeheader()
        writer.writerows(rows)
    return name


@pytest.fixture()
def datasets():
    reference = _write(
        "cmp_reference.csv",
        [{"amount": value, "velocity": 1, "distance": 10, "country": "US"} for value in range(100, 200)],
    )
    current = _write(
        "cmp_current.csv",
        [
            {"amount": value, "velocity": 9, "distance": 900, "country": "NG" if value % 2 else "US"}
            for value in range(500, 600)
        ],
    )
    yield reference, current
    for name in (reference, current):
        (DATA_DIR / name).unlink(missing_ok=True)


@pytest.fixture()
def api(app):
    with TestClient(app) as client:
        login = client.post("/api/v1/auth/login", data={"username": "analyst", "password": "analyst123"})
        client.headers.update({"Authorization": f"Bearer {login.json()['access_token']}"})
        yield client


def test_compare_supports_multiple_features(api, datasets):
    reference, current = datasets
    response = api.post("/api/v1/datasets/compare", json={"reference": reference, "current": current, "features": NUMERIC})
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["featureCount"] == len(NUMERIC)
    assert {item["feature"] for item in payload["features"]} == set(NUMERIC)
    assert payload["overallScore"] >= 0.0


def test_compare_defaults_to_every_shared_feature(api, datasets):
    reference, current = datasets
    payload = api.post("/api/v1/datasets/compare", json={"reference": reference, "current": current}).json()
    assert payload["featureCount"] == len(NUMERIC) + len(CATEGORICAL)
    assert set(payload["sharedFeatures"]) == {*NUMERIC, *CATEGORICAL}


def test_compare_includes_numeric_and_categorical_features(api, datasets):
    reference, current = datasets
    payload = api.post("/api/v1/datasets/compare", json={"reference": reference, "current": current}).json()
    kinds = {item["feature"]: item["type"] for item in payload["features"]}
    assert kinds["amount"] == "numeric"
    assert kinds["country"] == "categorical"


def test_compare_still_accepts_a_single_feature(api, datasets):
    reference, current = datasets
    payload = api.post("/api/v1/datasets/compare", json={"reference": reference, "current": current, "feature": "amount"}).json()
    assert payload["feature"] == "amount"
    assert payload["featureCount"] == 1
    assert "driftScore" in payload
    assert "bins" in payload


def test_each_feature_reports_its_own_drift(api, datasets):
    reference, current = datasets
    payload = api.post("/api/v1/datasets/compare", json={"reference": reference, "current": current}).json()
    scores = {item["feature"]: item["driftScore"] for item in payload["features"]}
    assert scores["amount"] > 0
    assert scores["distance"] > 0
    assert all(item["status"] in {"normal", "watch", "high"} for item in payload["features"])


def test_compare_rejects_an_unknown_feature(api, datasets):
    reference, current = datasets
    response = api.post("/api/v1/datasets/compare", json={"reference": reference, "current": current, "features": ["nope"]})
    assert response.status_code == 400


def test_compare_requires_authentication(app, datasets):
    reference, current = datasets
    with TestClient(app) as client:
        response = client.post("/api/v1/datasets/compare", json={"reference": reference, "current": current})
    assert response.status_code in (401, 403)


def test_unknown_dataset_is_not_found(api):
    response = api.post("/api/v1/datasets/compare", json={"reference": "missing.csv", "current": "missing.csv"})
    assert response.status_code == 404