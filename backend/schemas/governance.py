from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PolicySchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    version: str = Field(default="1.0")
    policy_type: str = Field(default="threshold")
    enabled: bool = True
    config: dict[str, Any] = Field(default_factory=dict)


class RiskScoreRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    probability: float
    drift_score: float = 0.0
    data_quality_score: float = 1.0
    policy_penalty: float = 0.0
    feature_risk_signals: dict[str, float] = Field(default_factory=dict)


class RiskScoreResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    risk_score: float
    components: dict[str, float]


class DecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    probability: float
    risk_score: float
    drift_score: float = 0.0
    policy_status: str = "pass"
    feature_risk_signals: dict[str, float] = Field(default_factory=dict)


class DecisionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision: str
    rationale: list[str] = Field(default_factory=list)
    risk_score: float
    policy_status: str
