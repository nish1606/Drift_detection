from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from sqlalchemy.orm import Session

from backend.database import crud
from backend.logging.logger import get_logger

logger = get_logger(__name__)


class DecisionLogger:
    def __init__(self, session: Session | None = None) -> None:
        self.session = session

    def log(self, *, actor: str, action: str, resource_type: str, resource_id: str, status: str, metadata: Mapping[str, Any] | None = None) -> None:
        payload = {
            "actor": actor,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "status": status,
            "metadata": dict(metadata or {}),
        }
        logger.info("decision event %s", payload)
        if self.session is not None:
            crud.create_audit_log(self.session, payload)
