from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from backend.database import crud


class AuditService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def record(self, **payload: Any):
        return crud.create_audit_log(self.session, payload)

    def latest(self, limit: int = 50) -> list[dict[str, Any]]:
        from backend.database.models import AuditLog
        from sqlalchemy import select

        rows = self.session.scalars(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)).all()
        return [
            {
                "actor": row.actor,
                "action": row.action,
                "resource_type": row.resource_type,
                "resource_id": row.resource_id,
                "status": row.status,
                "metadata": row.payload,
                "created_at": row.created_at.isoformat(),
            }
            for row in rows
        ]
