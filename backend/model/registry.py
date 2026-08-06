from __future__ import annotations

from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from backend.database import crud


def register_model_artifact(session: Session, *, name: str, version: str, uri: str, metrics: dict[str, Any], schema: dict[str, Any] | None = None) -> None:
    crud.create_model_artifact(
        session,
        {
            "name": name,
            "version": version,
            "uri": uri,
            "metrics": metrics,
            "schema": schema or {},
            "status": "active",
            "active": True,
        },
    )


def resolve_model_path(uri: str) -> Path:
    if uri.startswith("file://"):
        return Path(uri.removeprefix("file://"))
    return Path(uri)
