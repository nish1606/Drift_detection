from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from backend.database import crud


class RetrainingService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def enqueue(self, *, model_name: str, trigger_reason: str, params: dict[str, Any] | None = None):
        return crud.create_retraining_job(
            self.session,
            {
                "model_name": model_name,
                "status": "queued",
                "trigger_reason": trigger_reason,
                "params": params or {},
                "metrics": {},
                "started_at": datetime.now(UTC),
                "finished_at": None,
            },
        )
