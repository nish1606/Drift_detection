from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ResponseStateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str = Field(default="manual", max_length=512, description="Why the transition was requested")


class ResponseStateResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model_name: str
    state: str
    current_version: str
    current_status: str
    available_versions: list[str] = Field(default_factory=list)
    audit_event: dict[str, Any] = Field(default_factory=dict)