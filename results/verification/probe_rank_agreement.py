from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from backend.explainability.lime_service import LimeService
from backend.explainability.shap_service import ShapService
from ml_model.train import FraudModelTrainer

BENCHMARK_FEATURES = {
    "account_age_days": 30,
    "amount": 1200,
    "avg_amount_last_30d": 800,
    "geo_distance": 150,
    "is_foreign": 1,
    "merchant_category": "travel",
    "new_device": 1,
    "transaction_hour": 23,
    "velocity_1h": 5,
}

frame = pd.read_csv("backend/data/transactions_realistic.csv")
features = frame.drop(columns=["isFraud"]).to_dict("records")
labels = frame["isFraud"].astype(int).tolist()

import tempfile
with tempfile.TemporaryDirectory() as directory:
    artifact = FraudModelTrainer(artifact_dir=directory).train(
        model_name="experiment", model_version="1", features=features, labels=labels
    )
    engineered = FraudModelTrainer(artifact_dir=directory).feature_engineer.build(BENCHMARK_FEATURES)
    vectorizer = artifact.pipeline.named_steps["vectorizer"]
    transformed = vectorizer.transform([engineered])
    scores = artifact.pipeline.named_steps["model"].coef_[0] * transformed[0]
    names = vectorizer.get_feature_names_out()
    coefficient_top = [name for _, name in sorted(zip(np.abs(scores), names, strict=False), reverse=True)[:5]]
    shap_values = ShapService().explain(artifact.pipeline, [BENCHMARK_FEATURES])
    shap_top = [name for name, _ in sorted(shap_values.items(), key=lambda item: abs(item[1]), reverse=True)[:5]]
    lime_values = LimeService().explain(artifact.pipeline, BENCHMARK_FEATURES)
    lime_top = [name for name, _ in sorted(lime_values.items(), key=lambda item: abs(item[1]), reverse=True)[:5]]

    print("coefficient_top:", coefficient_top)
    print("shap_top:       ", shap_top)
    print("lime_top:       ", lime_top)

    union = sorted(set(shap_top) | set(lime_top))
    shap_ranks = [shap_top.index(name) if name in shap_top else 5 for name in union]
    lime_ranks = [lime_top.index(name) if name in lime_top else 5 for name in union]
    print("shap_ranks:", shap_ranks)
    print("lime_ranks:", lime_ranks)
    print("spearmanr(shap, lime):", float(spearmanr(shap_ranks, lime_ranks).statistic))

    union2 = sorted(set(coefficient_top) | set(shap_top))
    c_ranks = [coefficient_top.index(name) if name in coefficient_top else 5 for name in union2]
    s_ranks = [shap_top.index(name) if name in shap_top else 5 for name in union2]
    print("spearmanr(coef, shap):", float(spearmanr(c_ranks, s_ranks).statistic))