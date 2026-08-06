from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.api.deps import db_dep
from backend.core.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check(session: Session = Depends(db_dep)) -> dict[str, str]:
    session.execute(text("SELECT 1"))
    settings = get_settings()
    return {"status": "ok", "environment": settings.environment, "app": settings.app_name}


@router.get("/ready")
def readiness_check(session: Session = Depends(db_dep)) -> dict[str, str]:
    session.execute(text("SELECT 1"))
    return {"status": "ready"}
