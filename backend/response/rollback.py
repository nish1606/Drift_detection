from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.core.exceptions import NotFoundError
from backend.database.models import ModelArtifact

#: Kept for callers that want a minimal rollback; the full state machine with
#: audit events lives in :class:`backend.response.freeze.ModelResponseService`.
ROLLBACK_STATUS = "rolled_back"


class RollbackService:
    def __init__(self, session: Session, actor: str = "system") -> None:
        self.session = session
        self.actor = actor

    def rollback(self, model_name: str) -> ModelArtifact:
        artifacts = list(
            self.session.scalars(
                select(ModelArtifact).where(ModelArtifact.name == model_name).order_by(ModelArtifact.created_at.desc())
            ).all()
        )
        if len(artifacts) < 2:
            raise NotFoundError(f"no previous artifact available for '{model_name}'")
        previous = artifacts[1]
        for artifact in artifacts:
            artifact.active = artifact.id == previous.id
            artifact.status = "active" if artifact.active else ROLLBACK_STATUS
        self.session.commit()
        self.session.refresh(previous)
        return previous