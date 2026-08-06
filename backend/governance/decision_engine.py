from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from backend.governance.policy_engine import PolicyEvaluation


@dataclass
class DecisionOutcome:
    decision: str
    rationale: list[str] = field(default_factory=list)
    risk_score: float = 0.0
    policy_status: str = "pass"
    metadata: dict[str, Any] = field(default_factory=dict)


class DecisionEngine:
    def __init__(self, review_threshold: float = 0.45, block_threshold: float = 0.75, freeze_threshold: float = 0.9) -> None:
        self.review_threshold = review_threshold
        self.block_threshold = block_threshold
        self.freeze_threshold = freeze_threshold

    def decide(self, *, probability: float, risk_score: float, drift_score: float = 0.0, policy_evaluations: list[PolicyEvaluation] | None = None, feature_risk_signals: dict[str, float] | None = None) -> DecisionOutcome:
        policy_evaluations = policy_evaluations or []
        feature_risk_signals = feature_risk_signals or {}
        rationale: list[str] = []
        decision = "allow"
        policy_status = "pass"
        if any(not evaluation.passed and evaluation.action in {"block", "freeze"} for evaluation in policy_evaluations):
            policy_status = "block"
            decision = "block"
            rationale.append("policy blocked the request")
        elif risk_score >= self.freeze_threshold or drift_score >= self.freeze_threshold:
            decision = "freeze"
            rationale.append("risk or drift exceeded freeze threshold")
        elif risk_score >= self.block_threshold or probability >= 0.95:
            decision = "block"
            rationale.append("risk exceeded block threshold")
        elif risk_score >= self.review_threshold or probability >= 0.6:
            decision = "review"
            rationale.append("request requires manual review")
        if feature_risk_signals:
            hottest = max(feature_risk_signals.items(), key=lambda item: float(item[1]))
            rationale.append(f"highest feature signal: {hottest[0]}={hottest[1]:.3f}")
        return DecisionOutcome(decision=decision, rationale=rationale, risk_score=risk_score, policy_status=policy_status, metadata={"probability": probability, "drift_score": drift_score})
