"""Probe how many iterations the scaled pipeline needs to converge on the real dataset."""
from __future__ import annotations

import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.exceptions import ConvergenceWarning
from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[2]
frame = pd.read_csv(ROOT / "backend" / "data" / "transactions_realistic.csv")
labels = frame["isFraud"].astype(int).tolist()

import sys

sys.path.insert(0, str(ROOT))
from backend.preprocessing.feature_engineering import FeatureEngineer

engineer = FeatureEngineer()
engineered = [engineer.build(row) for row in frame.drop(columns=["isFraud"]).to_dict("records")]
train_x, test_x, train_y, test_y = train_test_split(engineered, labels, test_size=0.25, random_state=42, stratify=labels)

results = []
for max_iter in (1000, 5000, 20000, 100000):
    pipeline = Pipeline([
        ("vectorizer", DictVectorizer(sparse=False)),
        ("scaler", StandardScaler(with_mean=False)),
        ("model", LogisticRegression(max_iter=max_iter, class_weight="balanced")),
    ])
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        pipeline.fit(train_x, train_y)
    results.append({
        "max_iter": max_iter,
        "n_iter_": int(pipeline.named_steps["model"].n_iter_),
        "convergence_warning": any(issubclass(i.category, ConvergenceWarning) for i in captured),
        "coef_sum": float(np.sum(pipeline.named_steps["model"].coef_)),
    })

print(json.dumps(results, indent=2))
