from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from backend.database import crud


class AlertingService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_alert(self, *, severity: str, message: str, alert_type: str, context: dict[str, Any] | None = None):
        return crud.create_alert(
            self.session,
            {
                "severity": severity,
                "message": message,
                "alert_type": alert_type,
                "context": context or {},
                "is_resolved": False,
            },
        )

    def escalate(self, *, message: str, context: dict[str, Any] | None = None):
        return self.create_alert(severity="high", message=message, alert_type="escalation", context=context)
