from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.core.exceptions import NotFoundError
from backend.database.models import (
    Alert,
    AuditLog,
    DriftMetric,
    GovernancePolicy,
    ModelArtifact,
    PredictionRecord,
    RetrainingJob,
    User,
)


def create_prediction_record(session: Session, payload: dict[str, Any]) -> PredictionRecord:
    record = PredictionRecord(**payload)
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def bulk_create_prediction_records(session: Session, payloads: list[dict[str, Any]]) -> list[PredictionRecord]:
    records = [PredictionRecord(**payload) for payload in payloads]
    session.add_all(records)
    session.commit()
    for record in records:
        session.refresh(record)
    return records


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


def register_model_artifact(session: Session, *, name: str, version: str, uri: str) -> ModelArtifact:
    """Register an on-disk artifact, keeping at most one active version per name.

    Freeze, unfreeze and rollback all operate on ``ModelArtifact`` rows, so an
    artifact that exists on disk but was never registered has nothing to act on.
    """
    statement = select(ModelArtifact).where(ModelArtifact.name == name, ModelArtifact.version == version)
    existing = session.scalar(statement)
    if existing is not None:
        existing.uri = uri
        session.commit()
        session.refresh(existing)
        return existing
    for other in session.scalars(select(ModelArtifact).where(ModelArtifact.name == name)).all():
        if other.active:
            other.active = False
            other.status = "superseded"
    artifact = ModelArtifact(name=name, version=version, uri=uri, status="active", active=True, metrics={}, schema={})
    session.add(artifact)
    session.commit()
    session.refresh(artifact)
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


def bulk_create_drift_metrics(session: Session, payloads: list[dict[str, Any]]) -> list[DriftMetric]:
    metrics = [DriftMetric(**payload) for payload in payloads]
    session.add_all(metrics)
    session.commit()
    for metric in metrics:
        session.refresh(metric)
    return metrics


def create_alert(session: Session, payload: dict[str, Any]) -> Alert:
    alert = Alert(**payload)
    session.add(alert)
    session.commit()
    session.refresh(alert)
    return alert


def bulk_create_alerts(session: Session, payloads: list[dict[str, Any]]) -> list[Alert]:
    alerts = [Alert(**payload) for payload in payloads]
    session.add_all(alerts)
    session.commit()
    for alert in alerts:
        session.refresh(alert)
    return alerts


def resolve_alert(session: Session, alert_id: int) -> Alert:
    alert = session.get(Alert, alert_id)
    if alert is None:
        raise NotFoundError(f"alert {alert_id} not found")
    alert.is_resolved = True
    alert.resolved_at = datetime.now(UTC)
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
    return log


def bulk_create_audit_logs(session: Session, payloads: list[dict[str, Any]]) -> list[AuditLog]:
    logs = []
    for payload in payloads:
        mapped_payload = dict(payload)
        if "metadata" in mapped_payload:
            mapped_payload["payload"] = mapped_payload.pop("metadata")
        logs.append(AuditLog(**mapped_payload))
    session.add_all(logs)
    session.commit()
    return logs


def list_predictions(session: Session, limit: int = 50) -> list[PredictionRecord]:
    statement = select(PredictionRecord).order_by(PredictionRecord.created_at.desc()).limit(limit)
    return list(session.scalars(statement).all())


def get_prediction_by_request_id(session: Session, request_id: str) -> PredictionRecord | None:
    return session.scalar(select(PredictionRecord).where(PredictionRecord.request_id == request_id))


def create_retraining_job(session: Session, payload: dict[str, Any]) -> RetrainingJob:
    job = RetrainingJob(**payload)
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def get_user_by_username(session: Session, username: str) -> User | None:
    return session.scalar(select(User).where(User.username == username))


def create_user(session: Session, payload: dict[str, Any]) -> User:
    user = User(**payload)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def update_retraining_job(session: Session, job_id: int, updates: Mapping[str, Any]) -> RetrainingJob:
    job = session.get(RetrainingJob, job_id)
    if job is None:
        raise NotFoundError(f"retraining job {job_id} not found")
    for key, value in updates.items():
        setattr(job, key, value)
    session.commit()
    session.refresh(job)
    return job
