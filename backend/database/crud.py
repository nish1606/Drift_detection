from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.core.exceptions import NotFoundError
from backend.database.models import Alert, AuditLog, DriftMetric, GovernancePolicy, ModelArtifact, PredictionRecord, RetrainingJob


def create_prediction_record(session: Session, payload: dict[str, Any]) -> PredictionRecord:
    record = PredictionRecord(**payload)
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def create_model_artifact(session: Session, payload: dict[str, Any]) -> ModelArtifact:
    artifact = ModelArtifact(**payload)
    session.add(artifact)
    session.commit()
    session.refresh(artifact)
    return artifact


def get_active_model(session: Session, name: str) -> ModelArtifact:
    statement = select(ModelArtifact).where(ModelArtifact.name == name, ModelArtifact.active.is_(True))
    artifact = session.scalar(statement)
    if artifact is None:
        raise NotFoundError(f"active model '{name}' not found")
    return artifact


def upsert_policy(session: Session, payload: dict[str, Any]) -> GovernancePolicy:
    statement = select(GovernancePolicy).where(GovernancePolicy.name == payload["name"])
    policy = session.scalar(statement)
    mapped_payload = {
        "name": payload["name"],
        "version": str(payload.get("version", "1.0")),
        "policy_type": str(payload.get("policy_type", "threshold")),
        "enabled": bool(payload.get("enabled", True)),
        "config": dict(payload),
    }
    if policy is None:
        policy = GovernancePolicy(**mapped_payload)
        session.add(policy)
    else:
        for key, value in mapped_payload.items():
            setattr(policy, key, value)
    session.commit()
    session.refresh(policy)
    return policy


def list_policies(session: Session) -> list[GovernancePolicy]:
    return list(session.scalars(select(GovernancePolicy).order_by(GovernancePolicy.name)).all())


def create_drift_metric(session: Session, payload: dict[str, Any]) -> DriftMetric:
    metric = DriftMetric(**payload)
    session.add(metric)
    session.commit()
    session.refresh(metric)
    return metric


def create_alert(session: Session, payload: dict[str, Any]) -> Alert:
    alert = Alert(**payload)
    session.add(alert)
    session.commit()
    session.refresh(alert)
    return alert


def resolve_alert(session: Session, alert_id: int) -> Alert:
    alert = session.get(Alert, alert_id)
    if alert is None:
        raise NotFoundError(f"alert {alert_id} not found")
    alert.is_resolved = True
    alert.resolved_at = datetime.now(timezone.utc)
    session.commit()
    session.refresh(alert)
    return alert


def create_audit_log(session: Session, payload: dict[str, Any]) -> AuditLog:
    mapped_payload = dict(payload)
    if "metadata" in mapped_payload:
        mapped_payload["payload"] = mapped_payload.pop("metadata")
    log = AuditLog(**mapped_payload)
    session.add(log)
    session.commit()
    session.refresh(log)
    return log


def create_retraining_job(session: Session, payload: dict[str, Any]) -> RetrainingJob:
    job = RetrainingJob(**payload)
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def update_retraining_job(session: Session, job_id: int, updates: Mapping[str, Any]) -> RetrainingJob:
    job = session.get(RetrainingJob, job_id)
    if job is None:
        raise NotFoundError(f"retraining job {job_id} not found")
    for key, value in updates.items():
        setattr(job, key, value)
    session.commit()
    session.refresh(job)
    return job
