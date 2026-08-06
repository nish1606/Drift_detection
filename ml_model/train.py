from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score

from ml_model.evaluate import EvaluationResult, evaluate_predictions
from backend.preprocessing.feature_engineering import FeatureEngineer


@dataclass
class TrainingArtifact:
    model_name: str
    model_version: str
    artifact_path: str
    metrics: dict[str, float | dict[str, int]]
    pipeline: Pipeline = field(repr=False)


class FraudModelTrainer:
    def __init__(self, artifact_dir: str = "ml_model/artifacts") -> None:
        self.artifact_dir = Path(artifact_dir)
        self.artifact_dir.mkdir(parents=True, exist_ok=True)
        self.feature_engineer = FeatureEngineer()

    def _build_pipeline(self) -> Pipeline:
        return Pipeline(
            steps=[
                ("vectorizer", DictVectorizer(sparse=False)),
                ("model", LogisticRegression(max_iter=1000, class_weight="balanced")),
            ]
        )

    def train(self, *, model_name: str, model_version: str, features: list[dict[str, Any]], labels: list[int]) -> TrainingArtifact:
        if len(features) != len(labels):
            raise ValueError("features and labels must have the same length")
        if not features:
            raise ValueError("training data cannot be empty")
        if len(set(labels)) < 2:
            raise ValueError("training labels must contain at least two classes")
        engineered = [self.feature_engineer.build(record) for record in features]
        train_x, test_x, train_y, test_y = train_test_split(engineered, labels, test_size=0.25, random_state=42, stratify=labels)
        pipeline = self._build_pipeline()
        pipeline.fit(train_x, train_y)
        probabilities = pipeline.predict_proba(test_x)[:, 1].tolist()
        evaluation = evaluate_predictions(test_y, probabilities)
        artifact_path = self.artifact_dir / f"{model_name}_{model_version}.joblib"
        joblib.dump(pipeline, artifact_path)

        feature_names = pipeline.named_steps["vectorizer"].get_feature_names_out().tolist()
        joblib.dump(feature_names, self.artifact_dir / "feature_columns.pkl")
        joblib.dump({"model_version": model_version}, self.artifact_dir / "model_meta.pkl")

        numeric_df = pd.DataFrame(engineered)
        if "amount" in numeric_df.columns:
            amounts = numeric_df["amount"].values
            hist, bin_edges = np.histogram(amounts, bins=50)
            probs = hist.astype(float) / hist.sum()
            np.savez(self.artifact_dir / "train_stats.npz", bin_edges=bin_edges, probs=probs)

        return TrainingArtifact(
            model_name=model_name,
            model_version=model_version,
            artifact_path=str(artifact_path),
            metrics=evaluation.as_dict(),
            pipeline=pipeline,
        )
