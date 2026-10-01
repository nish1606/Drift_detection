from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.core.exceptions import ConflictError, NotFoundError
from backend.database.models import ModelArtifact
from backend.logging.decision_logger import DecisionLogger

#: Statuses an artifact may hold.
STATUS_ACTIVE = "active"
STATUS_FROZEN = "frozen"
STATUS_ROLLED_BACK = "rolled_back"
STATUS_SUPERSEDED = "superseded"


def list_artifacts(session: Session, model_name: str) -> list[ModelArtifact]:
    return list(
        session.scalars(
            select(ModelArtifact)
            .where(ModelArtifact.name == model_name)
            .order_by(ModelArtifact.created_at.desc(), ModelArtifact.id.desc())
        ).all()
    )


class ModelResponseService:
    """Freeze, unfreeze and rollback transitions for a model, with audit events.

    Every transition is validated against the artifact's current status so an
    out-of-order or repeated call is rejected instead of silently corrupting
    which artifact is serving traffic.
    """

    def __init__(self, session: Session, actor: str) -> None:
        self.session = session
        self.actor = actor
        self.audit = DecisionLogger(session)

    def state(self, model_name: str) -> dict[str, object]:
        artifacts = list_artifacts(self.session, model_name)
        if not artifacts:
            raise NotFoundError(f"model '{model_name}' has no artifacts")
        active = next((artifact for artifact in artifacts if artifact.active), None)
        frozen = next((artifact for artifact in artifacts if artifact.status == STATUS_FROZEN), None)
        current = active or frozen or artifacts[0]
        return {
            "model_name": model_name,
            "state": "frozen" if current.status == STATUS_FROZEN else ("active" if current.active else "inactive"),
            "current_version": current.version,
            "current_status": current.status,
            "available_versions": [artifact.version for artifact in artifacts],
        }

    def freeze(self, model_name: str, reason: str) -> dict[str, object]:
        artifacts = list_artifacts(self.session, model_name)
        if not artifacts:
            raise NotFoundError(f"model '{model_name}' has no artifacts")
        already_frozen = [artifact for artifact in artifacts if artifact.status == STATUS_FROZEN]
        if already_frozen:
            raise ConflictError(f"model '{model_name}' is already frozen at version '{already_frozen[0].version}'")
        active = [artifact for artifact in artifacts if artifact.active]
        if not active:
            raise ConflictError(f"model '{model_name}' has no active artifact to freeze")
        for artifact in active:
            artifact.status = STATUS_FROZEN
            artifact.active = False
        self.audit.log(
            actor=self.actor,
            action="model.freeze",
            resource_type="model",
            resource_id=model_name,
            status=STATUS_FROZEN,
            metadata={"reason": reason, "version": active[0].version, "previous_status": STATUS_ACTIVE},
        )
        self.session.commit()
        return self.state(model_name)

    def unfreeze(self, model_name: str, reason: str) -> dict[str, object]:
        artifacts = list_artifacts(self.session, model_name)
        frozen = [artifact for artifact in artifacts if artifact.status == STATUS_FROZEN]
        if not frozen:
            raise ConflictError(f"model '{model_name}' is not frozen")
        target = frozen[0]
        for artifact in artifacts:
            if artifact.active:
                artifact.status = STATUS_SUPERSEDED
                artifact.active = False
        target.status = STATUS_ACTIVE
        target.active = True
        self.audit.log(
            actor=self.actor,
            action="model.unfreeze",
            resource_type="model",
            resource_id=model_name,
            status=STATUS_ACTIVE,
            metadata={"reason": reason, "version": target.version},
        )
        self.session.commit()
        return self.state(model_name)

    def rollback(self, model_name: str, reason: str) -> dict[str, object]:
        artifacts = list_artifacts(self.session, model_name)
        if len(artifacts) < 2:
            raise NotFoundError(f"no previous artifact available for '{model_name}'")
        current = next((artifact for artifact in artifacts if artifact.active), None)
        # A frozen artifact was deliberately taken out of service, so it is not a
        # valid rollback target; restore the newest version that is still eligible.
        previous = next(
            (
                artifact
                for artifact in artifacts
                if not artifact.active
                and artifact.status != STATUS_FROZEN
                and (current is None or artifact.id != current.id)
            ),
            None,
        )
        if previous is None:
            raise ConflictError(f"model '{model_name}' has no earlier version to roll back to")
        for artifact in artifacts:
            artifact.active = artifact.id == previous.id
            if artifact.id == previous.id:
                artifact.status = STATUS_ACTIVE
            elif current is not None and artifact.id == current.id:
                artifact.status = STATUS_ROLLED_BACK
            elif not artifact.active:
                artifact.status = STATUS_SUPERSEDED
        self.audit.log(
            actor=self.actor,
            action="model.rollback",
            resource_type="model",
            resource_id=model_name,
            status=STATUS_ROLLED_BACK,
            metadata={
                "reason": reason,
                "from_version": current.version if current else None,
                "to_version": previous.version,
            },
        )
        self.session.commit()
        return self.state(model_name)


class FreezeService:
    """Backwards-compatible wrapper around :class:`ModelResponseService`."""

    def __init__(self, session: Session, actor: str = "system") -> None:
        self.service = ModelResponseService(session, actor=actor)

    def freeze_model(self, model_name: str) -> ModelArtifact:
        self.service.freeze(model_name, reason="FreezeService.freeze_model")
        return self._current(model_name)

    def unfreeze_model(self, model_name: str) -> ModelArtifact:
        self.service.unfreeze(model_name, reason="FreezeService.unfreeze_model")
        return self._current(model_name)

    def rollback_model(self, model_name: str) -> ModelArtifact:
        self.service.rollback(model_name, reason="FreezeService.rollback_model")
        return self._current(model_name)

    def state(self, model_name: str) -> dict[str, object]:
        return self.service.state(model_name)

    def _current(self, model_name: str) -> ModelArtifact:
        artifacts = list_artifacts(self.service.session, model_name)
        frozen = next((artifact for artifact in artifacts if artifact.status == STATUS_FROZEN), None)
        active = next((artifact for artifact in artifacts if artifact.active), None)
        target = frozen or active or artifacts[0]
        self.service.session.refresh(target)
        return target