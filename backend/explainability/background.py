from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from backend.preprocessing.feature_engineering import FeatureEngineer

BACKGROUND_ARTIFACT = Path(__file__).resolve().parents[2] / "ml_model" / "artifacts" / "training_background.pkl"


def sample_training_background(limit: int = 200) -> list[dict[str, Any]]:
    """Sample the shipped training CSV; used when no persisted background exists."""
    path = Path(__file__).resolve().parent.parent / "data" / "transactions_realistic.csv"
    frame = pd.read_csv(path).drop(columns=["isFraud"], errors="ignore")
    frame = frame if limit is None or limit <= 0 else frame.sample(limit, random_state=42)
    engineer = FeatureEngineer()
    records = frame.to_dict("records")
    records = [{key: (None if isinstance(value, float) and pd.isna(value) else value) for key, value in record.items()} for record in records]
    return [engineer.build(record) for record in records]


def training_background(limit: int = 200) -> list[dict[str, Any]]:
    """Background sample for local explanations.

    Prefers the rows persisted by ``ml_model.train`` so the explanation is built
    against the distribution the loaded model actually learned; falls back to a
    seeded sample of the shipped CSV when no artifact is present.
    """
    if BACKGROUND_ARTIFACT.exists():
        try:
            import joblib

            rows = joblib.load(BACKGROUND_ARTIFACT)
        except Exception:
            rows = None
        if rows:
            return [dict(row) for row in rows[:limit]] if limit else [dict(row) for row in rows]
    return sample_training_background(limit)