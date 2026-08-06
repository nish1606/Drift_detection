from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class StatisticalDriftRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reference: dict[str, list[float]]
    current: dict[str, list[float]]
    threshold: float = 0.2


class StatisticalDriftResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    drift_score: float
    drifted_features: list[str] = Field(default_factory=list)
    feature_scores: dict[str, float] = Field(default_factory=dict)


class SemanticDriftRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reference_texts: list[str]
    current_texts: list[str]


class DataQualityRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    records: list[dict[str, Any]]
