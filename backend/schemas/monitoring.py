from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DriftMetricSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    detector_name: str
    feature_name: str
    metric_value: float
    threshold: float
    status: str
    details: dict[str, Any] = Field(default_factory=dict)


class AlertSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    severity: str
    message: str
    alert_type: str
    context: dict[str, Any] = Field(default_factory=dict)
    is_resolved: bool = False


class AuditLogSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    actor: str
    action: str
    resource_type: str
    resource_id: str
    status: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvaluationMetricsSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    accuracy: float
    precision: float
    recall: float
    f1: float
    roc_auc: float
    confusion: dict[str, int] = Field(default_factory=dict)
