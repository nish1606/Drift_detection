from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PredictionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str | None = Field(default=None, max_length=64)
    model_name: str = Field(default="fraud_classifier", max_length=128)
    model_version: str | None = Field(default=None, max_length=64)
    features: dict[str, Any]
    metadata: dict[str, Any] = Field(default_factory=dict)


class PredictionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str
    model_name: str
    model_version: str
    prediction: int
    probability: float
    risk_score: float
    decision: str
    explanations: dict[str, Any] = Field(default_factory=dict)
    alerts: list[dict[str, Any]] = Field(default_factory=list)


class TrainingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model_name: str = Field(default="fraud_classifier")
    features: list[dict[str, Any]]
    labels: list[int]
    model_version: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class TrainingResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model_name: str
    model_version: str
    artifact_uri: str
    metrics: dict[str, float]
