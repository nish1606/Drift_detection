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
from sklearn.preprocessing import StandardScaler
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


BACKGROUND_SIZE = 512
BACKGROUND_SEED = 42


def _background_rows(rows: list[dict[str, Any]], size: int) -> list[dict[str, float]]:
    """Deterministic sample of the training rows used as the explanation background."""
    if len(rows) <= size:
        return [dict(row) for row in rows]
    rng = np.random.default_rng(BACKGROUND_SEED)
    indices = np.sort(rng.choice(len(rows), size=size, replace=False))
    return [dict(rows[int(index)]) for index in indices]


DEFAULT_MAX_ITER = 1000
SCALED_MAX_ITER = 10000


class FraudModelTrainer:
    def __init__(
        self,
        artifact_dir: str = "ml_model/artifacts",
        scale_features: bool = False,
        max_iter: int | None = None,
    ) -> None:
        self.artifact_dir = Path(artifact_dir)
        self.artifact_dir.mkdir(parents=True, exist_ok=True)
        self.feature_engineer = FeatureEngineer()
        self.scale_features = scale_features
        # The legacy unscaled pipeline keeps max_iter=1000 for backwards
        # compatibility with the reported paper numbers. The scaled pipeline is
        # the recommended configuration: standardising the engineered features
        # lets LBFGS converge well inside the default budget, and the raised
        # ceiling keeps it converging when the feature set grows.
        self.max_iter = max_iter if max_iter is not None else (SCALED_MAX_ITER if scale_features else DEFAULT_MAX_ITER)

    def _build_pipeline(self) -> Pipeline:
        steps = [("vectorizer", DictVectorizer(sparse=False))]
        if self.scale_features:
            steps.append(("scaler", StandardScaler(with_mean=False)))
        steps.append(("model", LogisticRegression(max_iter=self.max_iter, class_weight="balanced")))
        return Pipeline(steps=steps)

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
        # Persist the real training rows so LIME/SHAP explain against the
        # distribution the model actually learned, not a sample from the CSV.
        background_rows = _background_rows(train_x, BACKGROUND_SIZE)
        joblib.dump(background_rows, self.artifact_dir / "training_background.pkl")

        numeric_df = pd.DataFrame(engineered)
        baseline = {}
        if "amount" in numeric_df.columns:
            amounts = numeric_df["amount"].values
            hist, bin_edges = np.histogram(amounts, bins=50)
            probs = hist.astype(float) / hist.sum()
            np.savez(self.artifact_dir / "train_stats.npz", bin_edges=bin_edges, probs=probs)

        for column in numeric_df.columns:
            values = numeric_df[column].values.astype(float)
            baseline[column] = {
                "mean": float(np.mean(values)),
                "std": float(np.std(values)),
                "min": float(np.min(values)),
                "max": float(np.max(values)),
            }
        joblib.dump(baseline, self.artifact_dir / "baseline_stats.pkl")

        return TrainingArtifact(
            model_name=model_name,
            model_version=model_version,
            artifact_path=str(artifact_path),
            metrics=evaluation.as_dict(),
            pipeline=pipeline,
        )
