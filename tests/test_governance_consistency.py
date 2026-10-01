"""The live governance endpoints must reproduce the offline governance cases."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.governance.decision_engine import DecisionEngine
from backend.governance.policy_engine import PolicyEvaluation
from backend.governance.risk_scoring import RiskScorer

# Mirrors run_experiments.GOVERNANCE_CASES.
CASES = [
    ("Low risk", 0.1, 0.1, [], "allow", None),
    ("Moderate p", 0.6, 0.4, [], "review", None),
    ("Moderate combined", 0.4, 0.4, [], "allow", None),
    ("High risk", 0.4, 0.8, [], "block", None),
    ("p>=0.95", 0.95, 0.4, [], "block", None),
    ("High drift", 0.4, 0.4, [], "freeze", 0.95),
    ("Poor data quality", 0.1, 0.2, [], "allow", None),
    ("Very high combined", 0.8, 0.8, [], "block", None),
    ("Policy block", 0.1, 0.1, [("block", False)], "block", None),
    ("Policy review only", 0.6, 0.1, [("review", True)], "review", None),
    ("Combined factors", 0.5, 0.45, [], "review", None),
]


@pytest.fixture()
def api(app):
    with TestClient(app) as client:
        login = client.post("/api/v1/auth/login", data={"username": "analyst", "password": "analyst123"})
        client.headers.update({"Authorization": f"Bearer {login.json()['access_token']}"})
        yield client


def _body(probability, risk, drift, evaluations):
    body = {"probability": probability, "risk_score": risk, "drift_score": drift or 0.0}
    if evaluations:
        body["policy_evaluations"] = [{"action": action, "passed": passed} for action, passed in evaluations]
    return body


@pytest.mark.parametrize("name,probability,risk,evaluations,expected,drift", CASES, ids=[case[0] for case in CASES])
def test_live_decision_matches_the_offline_engine(api, name, probability, risk, evaluations, expected, drift):
    response = api.post("/api/v1/decision", json=_body(probability, risk, drift, evaluations))
    assert response.status_code == 200, response.text
    assert response.json()["decision"] == expected, name


@pytest.mark.parametrize("name,probability,risk,evaluations,expected,drift", CASES, ids=[case[0] for case in CASES])
def test_live_decision_matches_run_experiments_ground_truth(api, name, probability, risk, evaluations, expected, drift):
    from run_experiments import GOVERNANCE_CASES, governance_results

    live = api.post("/api/v1/decision", json=_body(probability, risk, drift, evaluations)).json()["decision"]
    offline = next(item for item in governance_results() if item["case"] == name)
    assert live == offline["decision"]
    assert offline["decision"] == offline["expected"]


def test_policy_evaluations_are_accepted(api):
    """The policy-block branch used to be unreachable over HTTP."""
    response = api.post(
        "/api/v1/decision",
        json={"probability": 0.01, "risk_score": 0.01, "policy_evaluations": [{"action": "block", "passed": False}]},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["decision"] == "block"
    assert payload["policy_status"] == "block"
    assert "policy blocked the request" in payload["rationale"]


def test_policy_review_does_not_block(api):
    payload = api.post(
        "/api/v1/decision",
        json={"probability": 0.6, "risk_score": 0.1, "policy_evaluations": [{"action": "review", "passed": True}]},
    ).json()
    assert payload["decision"] == "review"
    assert payload["policy_status"] == "pass"


def test_decision_reports_the_thresholds_it_used(api):
    payload = api.post("/api/v1/decision", json={"probability": 0.5, "risk_score": 0.5}).json()
    assert payload["thresholds"]["review_threshold"] == 0.45
    assert payload["thresholds"]["block_threshold"] == 0.75
    assert payload["thresholds"]["freeze_threshold"] == 0.9


def test_live_risk_score_equals_the_offline_scorer(api):
    """POST /risk-score must agree with RiskScorer for the same inputs."""
    for probability, drift in [(0.05, 0.0), (0.6, 0.0), (0.4, 0.8), (0.95, 0.2)]:
        live = api.post("/api/v1/risk-score", json={"probability": probability, "drift_score": drift}).json()
        expected = RiskScorer().score(probability=probability, drift_score=drift)
        assert live["risk_score"] == pytest.approx(expected["risk_score"])
        assert live["components"] == pytest.approx(expected["components"])


def test_supplied_risk_is_the_quantity_the_decision_engine_consumes(api):
    """Risk passed to /decision must be returned unchanged, not recomputed."""
    payload = api.post("/api/v1/decision", json={"probability": 0.4, "risk_score": 0.8}).json()
    assert payload["risk_score"] == 0.8
    offline = DecisionEngine().decide(probability=0.4, risk_score=0.8)
    assert payload["decision"] == offline.decision


def test_risk_score_uses_raw_psi_when_supplied(api):
    from backend.governance.drift_signal import drift_signal_from_psi

    psi = 0.5
    live = api.post("/api/v1/risk-score", json={"probability": 0.2, "raw_psi": psi}).json()
    expected = RiskScorer().score(probability=0.2, drift_score=drift_signal_from_psi(psi))
    assert live["risk_score"] == pytest.approx(expected["risk_score"])


def test_decision_requires_authentication(app):
    with TestClient(app) as client:
        response = client.post("/api/v1/decision", json={"probability": 0.5, "risk_score": 0.5})
    assert response.status_code in (401, 403)


def test_unknown_policy_evaluation_field_is_rejected(api):
    response = api.post(
        "/api/v1/decision",
        json={"probability": 0.5, "risk_score": 0.5, "policy_evaluations": [{"action": "block", "passed": False, "bogus": 1}]},
    )
    assert response.status_code == 422