"""Freeze/unfreeze/rollback must be reachable, authenticated and audited."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.database import crud


def _artifact(version: str, *, active: bool, status: str = "active"):
    return {
        "name": "fraud_classifier",
        "version": version,
        "uri": f"artifacts/{version}.joblib",
        "status": status,
        "active": active,
        "metrics": {},
        "schema": {},
    }


@pytest.fixture()
def api(app, db_session):
    crud.create_model_artifact(db_session, _artifact("1.0", active=True))
    crud.create_model_artifact(db_session, _artifact("2.0", active=False, status="superseded"))
    db_session.commit()
    with TestClient(app) as client:
        login = client.post("/api/v1/auth/login", data={"username": "analyst", "password": "analyst123"})
        assert login.status_code == 200
        client.headers.update({"Authorization": f"Bearer {login.json()['access_token']}"})
        yield client


TRANSITIONS = ["freeze", "unfreeze", "rollback"]


@pytest.mark.parametrize("path", [f"/api/v1/models/fraud_classifier/{name}" for name in TRANSITIONS] + ["/api/v1/models/fraud_classifier/response-state"])
def test_response_endpoints_require_authentication(path):
    from backend.app import create_app
    from backend.core.config import Settings
    import tempfile, os

    settings = Settings(
        database_url=f"sqlite:///{os.path.join(tempfile.mkdtemp(), 'fraud.db')}",
        model_store_path=os.path.join(tempfile.mkdtemp(), "artifacts"),
        policies_path="backend/governance/policies",
        allow_docs=False,
    )
    with TestClient(create_app(settings)) as client:
        if path.endswith("response-state"):
            response = client.get(path)
        else:
            response = client.post(path, json={})
        assert response.status_code in (401, 403), response.text


def test_response_state_is_readable(api):
    response = api.get("/api/v1/models/fraud_classifier/response-state")
    assert response.status_code == 200
    payload = response.json()
    assert payload["model_name"] == "fraud_classifier"
    assert payload["state"] == "active"
    assert payload["current_version"] == "1.0"


def test_freeze_transitions_to_frozen_and_is_audited(api):
    response = api.post("/api/v1/models/fraud_classifier/freeze", json={"reason": "drift spike"})
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["state"] == "frozen"
    assert payload["current_status"] == "frozen"

    audits = api.get("/api/v1/audit").json()
    events = [item for item in audits if item["action"] == "model.freeze"]
    assert events, audits
    assert events[0]["resource_id"] == "fraud_classifier"
    assert events[0]["metadata"]["reason"] == "drift spike"


def test_double_freeze_is_rejected(api):
    assert api.post("/api/v1/models/fraud_classifier/freeze", json={"reason": "one"}).status_code == 200
    conflict = api.post("/api/v1/models/fraud_classifier/freeze", json={"reason": "two"})
    assert conflict.status_code == 409
    assert "already frozen" in conflict.json()["detail"]


def test_unfreeze_returns_the_model_to_active(api):
    api.post("/api/v1/models/fraud_classifier/freeze", json={"reason": "drift"})
    payload = api.post("/api/v1/models/fraud_classifier/unfreeze", json={"reason": "drift cleared"}).json()
    assert payload["state"] == "active"
    assert payload["current_version"] == "1.0"
    actions = [item["action"] for item in api.get("/api/v1/audit").json()]
    assert "model.unfreeze" in actions


def test_unfreeze_without_a_freeze_is_rejected(api):
    response = api.post("/api/v1/models/fraud_classifier/unfreeze", json={"reason": "nope"})
    assert response.status_code == 409
    assert "not frozen" in response.json()["detail"]


def test_rollback_activates_the_previous_version(api):
    payload = api.post("/api/v1/models/fraud_classifier/rollback", json={"reason": "bad release"}).json()
    assert payload["current_version"] == "2.0"
    assert payload["current_status"] == "active"
    events = [item for item in api.get("/api/v1/audit").json() if item["action"] == "model.rollback"]
    assert events
    assert events[0]["metadata"]["from_version"] == "1.0"
    assert events[0]["metadata"]["to_version"] == "2.0"


def test_rollback_is_idempotent_in_direction(api):
    api.post("/api/v1/models/fraud_classifier/rollback", json={"reason": "bad release"})
    payload = api.post("/api/v1/models/fraud_classifier/rollback", json={"reason": "again"}).json()
    assert payload["current_version"] == "1.0"


def test_rollback_without_history_is_not_found(app, db_session):
    crud.create_model_artifact(db_session, _artifact("1.0", active=True))
    db_session.commit()
    with TestClient(app) as client:
        login = client.post("/api/v1/auth/login", data={"username": "analyst", "password": "analyst123"})
        client.headers.update({"Authorization": f"Bearer {login.json()['access_token']}"})
        response = client.post("/api/v1/models/fraud_classifier/rollback", json={"reason": "nope"})
    assert response.status_code == 404


def test_freeze_then_rollback_switches_serving_version(api):
    api.post("/api/v1/models/fraud_classifier/freeze", json={"reason": "drift"})
    payload = api.post("/api/v1/models/fraud_classifier/rollback", json={"reason": "serve older"}).json()
    assert payload["state"] == "active"
    assert payload["current_version"] == "2.0"