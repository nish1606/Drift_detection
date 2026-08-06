from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.api.deps import db_dep, metrics_dep
from backend.database.models import Alert, AuditLog, DriftMetric
from backend.monitoring.audit import AuditService
from backend.monitoring.dashboard import MonitoringDashboard
from backend.monitoring.metrics import MetricsCollector

router = APIRouter(tags=["monitoring"])


@router.get("/metrics")
def metrics_endpoint(collector: MetricsCollector = Depends(metrics_dep)) -> dict[str, object]:
    dashboard = MonitoringDashboard(collector)
    return {"metrics": dashboard.collector.snapshot(), "prometheus": dashboard.collector.prometheus_text()}


@router.get("/dashboard")
def dashboard_endpoint(session: Session = Depends(db_dep), collector: MetricsCollector = Depends(metrics_dep)) -> dict[str, object]:
    recent_alerts = [
        {
            "id": alert.id,
            "severity": alert.severity,
            "message": alert.message,
            "alert_type": alert.alert_type,
            "is_resolved": alert.is_resolved,
        }
        for alert in session.scalars(select(Alert).order_by(Alert.created_at.desc()).limit(20)).all()
    ]
    drift_summary = {"count": len(session.scalars(select(DriftMetric)).all())}
    audit_summary = {"count": len(AuditService(session).latest(20))}
    dashboard = MonitoringDashboard(collector)
    return dashboard.build(recent_alerts=recent_alerts, drift_summary=drift_summary, audit_summary=audit_summary)


@router.get("/audit")
def audit_endpoint(session: Session = Depends(db_dep)) -> list[dict[str, object]]:
    return AuditService(session).latest(50)
