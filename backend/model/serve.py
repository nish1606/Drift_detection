from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from backend.database import crud
from backend.model.predict import FraudPredictor, PredictionResult
from backend.model.registry import resolve_model_path
from backend.model.train import FraudModelTrainer, TrainingArtifact


@dataclass
class FraudModelService:
    session: Session
    artifact_dir: str = "./artifacts"

    def _latest_model_path(self, model_name: str) -> str | None:
        try:
            artifact = crud.get_active_model(self.session, model_name)
        except Exception:
            return None
        return str(resolve_model_path(artifact.uri))

    def predict(self, *, model_name: str, model_version: str | None, features: dict[str, Any]) -> PredictionResult:
        predictor = FraudPredictor(
            model_path=self._latest_model_path(model_name),
            model_name=model_name,
            model_version=model_version or "1.0.0",
        )
        return predictor.predict(features)

    def train(self, *, model_name: str, model_version: str, features: list[dict[str, Any]], labels: list[int]) -> TrainingArtifact:
        trainer = FraudModelTrainer(artifact_dir=self.artifact_dir)
        artifact = trainer.train(model_name=model_name, model_version=model_version, features=features, labels=labels)
        crud.create_model_artifact(
            self.session,
            {
                "name": model_name,
                "version": model_version,
                "uri": artifact.artifact_path,
                "metrics": artifact.metrics,
                "schema": {},
                "status": "active",
                "active": True,
            },
        )
        return artifact
