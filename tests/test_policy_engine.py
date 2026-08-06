from __future__ import annotations

from backend.governance.policy_engine import PolicyEngine
from backend.governance.policy_loader import PolicyLoader


def test_policy_loader_reads_yaml():
    policies = PolicyLoader("backend/governance/policies").load()
    assert policies


def test_policy_engine_evaluates_thresholds():
    engine = PolicyEngine(PolicyLoader("backend/governance/policies").load())
    evaluations = engine.evaluate({"probability": 0.95, "risk_score": 0.9, "fairness_gap": 0.2})
    assert evaluations
    assert any(evaluation.action in {"block", "review"} for evaluation in evaluations)
