from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from backend.preprocessing.feature_engineering import FeatureEngineer


def training_background(limit: int = 200) -> list[dict[str, Any]]:
    path = Path(__file__).resolve().parent.parent / "data" / "transactions_realistic.csv"
    frame = pd.read_csv(path).drop(columns=["isFraud"], errors="ignore").sample(limit, random_state=42)
    engineer = FeatureEngineer()
    records = frame.to_dict("records")
    records = [{key: (None if isinstance(value, float) and pd.isna(value) else value) for key, value in record.items()} for record in records]
    return [engineer.build(record) for record in records]