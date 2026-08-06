from __future__ import annotations

from backend.governance.decision_engine import DecisionEngine
from backend.governance.policy_engine import PolicyEvaluation


def test_decision_engine_blocks_on_policy_failure():
    engine = DecisionEngine()
    outcome = engine.decide(
        probability=0.95,
        risk_score=0.95,
        policy_evaluations=[PolicyEvaluation(policy_name="fraud", passed=False, action="block")],
    )
    assert outcome.decision == "block"


def test_decision_engine_reviews_medium_risk():
    engine = DecisionEngine()
    outcome = engine.decide(probability=0.6, risk_score=0.5)
    assert outcome.decision == "review"
