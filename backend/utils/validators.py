from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from backend.core.exceptions import ValidationError


def validate_feature_payload(payload: Mapping[str, Any]) -> None:
    if not isinstance(payload, Mapping):
        raise ValidationError("features must be a mapping")
    if not payload:
        raise ValidationError("features cannot be empty")


def validate_probability(probability: float) -> None:
    if probability < 0.0 or probability > 1.0:
        raise ValidationError("probability must be within [0, 1]")


def validate_policy_config(config: Mapping[str, Any]) -> None:
    if not isinstance(config, Mapping):
        raise ValidationError("policy config must be a mapping")
    if "rules" not in config:
        raise ValidationError("policy config requires rules")
