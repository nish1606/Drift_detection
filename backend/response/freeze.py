from __future__ import annotations

from sqlalchemy.orm import Session

from backend.database import crud
from backend.database.models import ModelArtifact


class FreezeService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def freeze_model(self, model_name: str) -> ModelArtifact:
        artifact = crud.get_active_model(self.session, model_name)
        artifact.status = "frozen"
        artifact.active = False
        self.session.commit()
        self.session.refresh(artifact)
        return artifact
