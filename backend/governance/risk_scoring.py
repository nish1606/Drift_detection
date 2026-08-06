from __future__ import annotations

from typing import Any

from backend.utils.constants import DEFAULT_RISK_THRESHOLD


class RiskScorer:
    def __init__(self, base_weight: float = 0.65, drift_weight: float = 0.2, data_quality_weight: float = 0.1, policy_weight: float = 0.05) -> None:
        self.base_weight = base_weight
        self.drift_weight = drift_weight
        self.data_quality_weight = data_quality_weight
        self.policy_weight = policy_weight

    def score(self, *, probability: float, drift_score: float = 0.0, data_quality_score: float = 1.0, policy_penalty: float = 0.0, feature_risk_signals: dict[str, float] | None = None) -> dict[str, Any]:
        feature_risk_signals = feature_risk_signals or {}
        signal_component = sum(max(0.0, min(1.0, float(value))) for value in feature_risk_signals.values())
        signal_component = min(signal_component / max(len(feature_risk_signals), 1), 1.0)
        risk = (
            self.base_weight * probability
            + self.drift_weight * drift_score
            + self.data_quality_weight * (1.0 - data_quality_score)
            + self.policy_weight * policy_penalty
            + 0.1 * signal_component
        )
        risk = max(0.0, min(risk, 1.0))
        return {
            "risk_score": risk,
            "components": {
                "probability": probability,
                "drift_score": drift_score,
                "data_quality_score": data_quality_score,
                "policy_penalty": policy_penalty,
                "feature_signal": signal_component,
                "threshold_hint": DEFAULT_RISK_THRESHOLD,
            },
        }
