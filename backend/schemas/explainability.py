from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class GradCAMRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model_name: str = Field(default="fraud_classifier", max_length=128)
    model_version: str | None = Field(default=None, max_length=64)
    features: dict[str, Any]


class ExplainabilityRequest(BaseModel):
    """Query-parameter form of :class:`GradCAMRequest` for the GET endpoints."""

    model_config = ConfigDict(extra="forbid")

    model_name: str = Field(default="fraud_classifier", max_length=128)
    model_version: str | None = Field(default=None, max_length=64)
    #: JSON object encoded as a single query parameter, e.g. ``?features={"amount":1200}``.
    features: str = Field(default="{}", description="JSON object of transaction features")

    def feature_dict(self) -> dict[str, Any]:
        try:
            parsed = json.loads(self.features)
        except json.JSONDecodeError as error:
            raise ValueError("features must be a JSON object") from error
        if not isinstance(parsed, dict):
            raise ValueError("features must be a JSON object")
        return parsed


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
