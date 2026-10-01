from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class GradCAMRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model_name: str = Field(default="fraud_classifier", max_length=128)
    model_version: str | None = Field(default=None, max_length=64)
    features: dict[str, Any]


class GradCAMResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    method: str
    model_name: str
    model_version: str
    prediction: int
    probability: float
    baseline: float
    attributions: list[dict[str, Any]]


class ExplainabilityResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    method: str
    values: dict[str, float]
