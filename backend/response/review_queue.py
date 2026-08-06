from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from backend.response.alerting import AlertingService


class ReviewQueueService:
    def __init__(self, session: Session) -> None:
        self.alerting = AlertingService(session)

    def enqueue(self, *, message: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        alert = self.alerting.create_alert(severity="medium", message=message, alert_type="manual_review", context=context)
        return {"alert_id": alert.id, "status": "queued"}
