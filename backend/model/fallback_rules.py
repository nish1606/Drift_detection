from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def rule_based_probability(features: Mapping[str, Any]) -> float:
    score = 0.0
    amount = float(features.get("amount", 0.0) or 0.0)
    is_high_risk_country = float(features.get("high_risk_country", 0.0) or 0.0)
    is_velocity_spike = float(features.get("velocity_spike", 0.0) or 0.0)
    is_new_device = float(features.get("new_device", 0.0) or 0.0)
    score += min(amount / 10000.0, 0.35)
    score += 0.2 * is_high_risk_country
    score += 0.2 * is_velocity_spike
    score += 0.15 * is_new_device
    return max(0.0, min(score, 1.0))


def rule_based_decision(probability: float, risk_score: float) -> str:
    if probability >= 0.9 or risk_score >= 0.9:
        return "block"
    if probability >= 0.6 or risk_score >= 0.6:
        return "review"
    return "allow"
