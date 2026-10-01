"""Artifacts must be registered so freeze/rollback have rows to act on."""
from __future__ import annotations

from backend.database import crud
from backend.database.models import ModelArtifact


def test_register_model_artifact_creates_an_active_row(db_session):
    artifact = crud.register_model_artifact(db_session, name="fraud_classifier", version="v1", uri="/tmp/v1.joblib")
    assert artifact.id is not None
    assert artifact.active is True
    assert artifact.status == "active"
    assert db_session.get(ModelArtifact, artifact.id) is not None


def test_registering_the_same_version_twice_is_idempotent(db_session):
    first = crud.register_model_artifact(db_session, name="m", version="v1", uri="/tmp/a.joblib")
    second = crud.register_model_artifact(db_session, name="m", version="v1", uri="/tmp/b.joblib")
    assert first.id == second.id
    assert second.uri == "/tmp/b.joblib"
    assert len(db_session.query(ModelArtifact).filter(ModelArtifact.name == "m").all()) == 1


def test_a_new_version_supersedes_the_previous_active_one(db_session):
    first = crud.register_model_artifact(db_session, name="m", version="v1", uri="/tmp/v1.joblib")
    second = crud.register_model_artifact(db_session, name="m", version="v2", uri="/tmp/v2.joblib")
    db_session.refresh(first)
    assert first.active is False
    assert first.status == "superseded"
    assert second.active is True
    assert crud.get_active_model(db_session, "m").version == "v2"


def test_registration_enables_freeze_and_rollback(db_session):
    from backend.response.freeze import ModelResponseService

    crud.register_model_artifact(db_session, name="fraud_classifier", version="v1", uri="/tmp/v1.joblib")
    crud.register_model_artifact(db_session, name="fraud_classifier", version="v2", uri="/tmp/v2.joblib")
    db_session.commit()

    service = ModelResponseService(db_session, actor="tester")
    assert service.state("fraud_classifier")["current_version"] == "v2"
    assert service.freeze("fraud_classifier", reason="test")["state"] == "frozen"
    assert service.rollback("fraud_classifier", reason="test")["current_version"] == "v1"