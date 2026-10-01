"""Every /api route except the documented bootstrap endpoints must reject anonymous callers."""
from __future__ import annotations

import pytest
from fastapi.routing import APIRoute

from backend.app import PUBLIC_PATHS

# Paths that must stay reachable without credentials.
BOOTSTRAP_PATHS = {"/api/v1/health", "/api/v1/ready", "/api/v1/auth/login", "/api/v1/auth/register"}

# Minimal bodies so an authenticated 401 is the only thing standing between an
# anonymous caller and the handler.
REQUEST_CASES = [
    ("GET", "/api/v1/audit", None),
    ("GET", "/api/v1/auth/me", None),
    ("GET", "/api/v1/dashboard", None),
    ("GET", "/api/v1/datasets", None),
    ("GET", "/api/v1/explainability/shap", {"amount": 1200.0, "transaction_hour": 23}),
    ("GET", "/api/v1/explainability/lime", {"amount": 1200.0, "transaction_hour": 23}),
    ("GET", "/api/v1/metrics", None),
    ("GET", "/api/v1/policies", None),
    ("GET", "/api/v1/policies/history", None),
    ("GET", "/api/v1/predictions", None),
    ("GET", "/api/v1/summary", None),
    ("GET", "/api/v1/transactions", None),
    ("POST", "/api/v1/datasets/compare", {"reference": "transactions_realistic.csv", "current": "transactions_realistic.csv"}),
    ("POST", "/api/v1/decision", {"probability": 0.9, "risk_score": 0.9}),
    ("POST", "/api/v1/drift/concept", [0.05, 0.06]),
    ("POST", "/api/v1/drift/data-quality", {"records": [{"amount": 1.0}]}),
    ("POST", "/api/v1/drift/semantic", {"reference_texts": ["a"], "current_texts": ["b"]}),
    ("POST", "/api/v1/drift/statistical", {"reference": {"amount": [1.0, 2.0]}, "current": {"amount": [9.0, 10.0]}}),
    ("POST", "/api/v1/explainability/grad-cam", {"features": {"amount": 1200.0}}),
    ("POST", "/api/v1/explainability/lime", {"features": {"amount": 1200.0}}),
    ("POST", "/api/v1/explainability/shap", {"features": {"amount": 1200.0}}),
    ("POST", "/api/v1/policies", {"name": "probe"}),
    ("POST", "/api/v1/policies/draft", {"name": "probe"}),
    ("POST", "/api/v1/policies/evaluate", {"probability": 0.9}),
    ("POST", "/api/v1/predict", {"features": {"amount": 1200.0}}),
    ("POST", "/api/v1/risk-score", {"probability": 0.9}),
    ("POST", "/api/v1/transactions/probe-id/status", {"status": "Reviewed"}),
]


def _api_paths(app) -> set[str]:
    return {
        route.path
        for route in app.routes
        if isinstance(route, APIRoute) and route.path.startswith("/api/")
    }


def test_bootstrap_paths_are_the_documented_ones():
    assert PUBLIC_PATHS == BOOTSTRAP_PATHS


def test_every_api_route_outside_bootstrap_returns_401(client):
    failures = []
    for method, path, body in REQUEST_CASES:
        if method == "GET":
            response = client.get(path)
        else:
            response = client.post(path, json=body)
        if response.status_code != 401:
            failures.append(f"{method} {path} -> {response.status_code}")
    assert not failures, f"anonymous access allowed on: {failures}"


def test_request_cases_cover_every_protected_route(app, client):
    """Guards against a new route being added without a matching 401 test."""
    covered = {path for _, path, _ in REQUEST_CASES}
    uncovered = sorted(path for path in _api_paths(app) if path not in BOOTSTRAP_PATHS and path not in covered)
    assert not uncovered, f"routes without an anonymous-access test: {uncovered}"


def test_bootstrap_endpoints_are_reachable_without_a_token(client):
    assert client.get("/api/v1/health").status_code == 200
    assert client.get("/api/v1/ready").status_code == 200
    assert client.post("/api/v1/auth/login", json={"username": "analyst", "password": "analyst123"}).status_code == 422
    assert client.post("/api/v1/auth/login", data={"username": "analyst", "password": "analyst123"}).status_code == 200


def test_malformed_token_is_rejected(client):
    for header in ("Bearer not-a-jwt", "analyst", "Bearer "):
        response = client.get("/api/v1/transactions", headers={"Authorization": header})
        assert response.status_code == 401, header


def test_transaction_status_update_requires_authentication(client):
    """The state-changing route must reject an anonymous caller."""
    anonymous = client.post("/api/v1/transactions/some-request-id/status", json={"status": "Reviewed"})
    assert anonymous.status_code == 401

    login = client.post("/api/v1/auth/login", data={"username": "analyst", "password": "analyst123"})
    token = login.json()["access_token"]
    authenticated = client.post(
        "/api/v1/transactions/some-request-id/status",
        json={"status": "Reviewed"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert authenticated.status_code == 200


@pytest.mark.parametrize("path", ["/api/v1/decision", "/api/v1/risk-score", "/api/v1/policies/evaluate"])
def test_governance_endpoints_require_authentication(client, path):
    assert client.post(path, json={"probability": 0.9, "risk_score": 0.9}).status_code == 401