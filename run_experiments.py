from __future__ import annotations

import json
import importlib.metadata
import tempfile
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.exceptions import ConvergenceWarning
from sklearn.metrics import average_precision_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score

from backend.detection.concept_drift import ConceptDriftDetector
from backend.detection.data_quality import DataQualityChecker
from backend.detection.semantic_drift import detect_semantic_drift
from backend.detection.statistical_drift import StatisticalDriftDetector
from backend.explainability.lime_service import LimeService
from backend.explainability.shap_service import ShapService
from backend.governance.decision_engine import DecisionEngine
from backend.governance.policy_engine import PolicyEvaluation
from ml_model.train import FraudModelTrainer

ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "backend" / "data" / "transactions_realistic.csv"
BENCHMARK_FEATURES = {
    "amount": 1200,
    "transaction_hour": 23,
    "is_foreign": 1,
    "velocity_1h": 5,
    "new_device": 1,
    "account_age_days": 30,
    "avg_amount_last_30d": 800,
    "merchant_category": "travel",
    "geo_distance": 150,
}


def _records_without_nan(frame: pd.DataFrame) -> list[dict[str, object]]:
    records = frame.to_dict("records")
    return [{key: (None if isinstance(value, float) and np.isnan(value) else value) for key, value in record.items()} for record in records]

GOVERNANCE_CASES = [
    ("Low risk", 0.1, 0.1, [] , "allow"),
    ("Moderate p", 0.6, 0.4, [], "review"),
    ("Moderate combined", 0.4, 0.4, [], "allow"),
    ("High risk", 0.4, 0.8, [], "block"),
    ("p>=0.95", 0.95, 0.4, [], "block"),
    ("High drift", 0.4, 0.4, [], "freeze", 0.95),
    ("Poor data quality", 0.1, 0.2, [], "allow"),
    ("Very high combined", 0.8, 0.8, [], "block"),
    ("Policy block", 0.1, 0.1, [PolicyEvaluation("block", False, "block")], "block"),
    ("Policy review only", 0.6, 0.1, [PolicyEvaluation("review", True, "review")], "review"),
    ("Combined factors", 0.5, 0.45, [], "review"),
]


def governance_results() -> list[dict[str, object]]:
    engine = DecisionEngine()
    results = []
    for case in GOVERNANCE_CASES:
        name, probability, risk, policies, expected, *drift = case
        outcome = engine.decide(probability=probability, risk_score=risk, drift_score=drift[0] if drift else 0.0, policy_evaluations=policies)
        results.append({"case": name, "decision": outcome.decision, "expected": expected, "matches": outcome.decision == expected})
    return results


def detector_results() -> dict[str, object]:
    detector = StatisticalDriftDetector()
    psi = detector._psi(np.array([1, 1, 1, 2, 2, 2]), np.array([100, 120, 150, 160, 170, 180]))
    concept = ConceptDriftDetector()
    first_trigger = None
    for observation, value in enumerate([0.05] * 30 + [0.30] * 45, 1):
        if concept.update(value) and first_trigger is None:
            first_trigger = observation
    constant = ConceptDriftDetector()
    constant_triggered = any(constant.update(0.05) for _ in range(75))
    return {"psi_fixture": psi, "psi_drifted": psi >= 0.2, "concept_first_trigger": first_trigger, "constant_triggered": constant_triggered}


def _metrics(labels: list[int], probabilities: np.ndarray, threshold: float = 0.5) -> dict[str, object]:
    predicted = (probabilities >= threshold).astype(int)
    matrix = confusion_matrix(labels, predicted, labels=[0, 1]).tolist()
    return {
        "roc_auc": float(roc_auc_score(labels, probabilities)),
        "precision": float(precision_score(labels, predicted, zero_division=0)),
        "recall": float(recall_score(labels, predicted, zero_division=0)),
        "f1": float(f1_score(labels, predicted, zero_division=0)),
        "confusion": matrix,
    }


def _fit_and_evaluate(features: list[dict[str, object]], labels: list[int], scale_features: bool, artifact_dir: str) -> tuple[dict[str, object], object]:
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        artifact = FraudModelTrainer(artifact_dir=artifact_dir, scale_features=scale_features).train(model_name="experiment", model_version="1", features=features, labels=labels)
    convergence = any(issubclass(item.category, ConvergenceWarning) for item in captured)
    return {**artifact.metrics, "convergence_warning": convergence}, artifact.pipeline


def model_results(frame: pd.DataFrame) -> dict[str, object]:
    features = _records_without_nan(frame.drop(columns=["isFraud"]))
    labels = frame["isFraud"].astype(int).tolist()
    with tempfile.TemporaryDirectory() as directory:
        legacy_metrics, legacy_pipeline = _fit_and_evaluate(features, labels, False, directory)
        scaled_metrics, _ = _fit_and_evaluate(features, labels, True, directory)
        engineer = FraudModelTrainer(artifact_dir=directory).feature_engineer
        engineered = [engineer.build(item) for item in features]
        probabilities = legacy_pipeline.predict_proba([engineered[index] for index in range(len(engineered))])[:, 1]
        threshold_metrics = {}
        for threshold in (0.3, 0.5, 0.7, 0.9):
            metric = _metrics(labels, probabilities, threshold)
            negatives = sum(label == 0 for label in labels)
            false_positive = metric["confusion"][0][1]
            metric["fpr"] = false_positive / negatives if negatives else 0.0
            threshold_metrics[str(threshold)] = metric
        threshold_metrics["average_precision"] = float(average_precision_score(labels, probabilities))

        ordered = frame.sort_values("timestamp")
        split = int(len(ordered) * 0.75)
        chronological_frame = ordered.drop(columns=["isFraud"])
        chronological_features = _records_without_nan(chronological_frame)
        chronological_labels = ordered["isFraud"].astype(int).tolist()
        chronological_engineered = [engineer.build(item) for item in chronological_features]
        pipeline = FraudModelTrainer(artifact_dir=directory)._build_pipeline()
        pipeline.fit(chronological_engineered[:split], chronological_labels[:split])
        chronological_probabilities = pipeline.predict_proba(chronological_engineered[split:])[:, 1]
        chronological_metrics = _metrics(chronological_labels[split:], chronological_probabilities)
    return {"legacy": legacy_metrics, "scaled": scaled_metrics, "threshold_analysis": threshold_metrics, "chronological split on synthetic data": chronological_metrics}


def explainability_results(frame: pd.DataFrame) -> dict[str, object]:
    features = _records_without_nan(frame.drop(columns=["isFraud"]))
    labels = frame["isFraud"].astype(int).tolist()
    with tempfile.TemporaryDirectory() as directory:
        artifact = FraudModelTrainer(artifact_dir=directory).train(model_name="experiment", model_version="1", features=features, labels=labels)
        engineered = FraudModelTrainer(artifact_dir=directory).feature_engineer.build(BENCHMARK_FEATURES)
        vectorizer = artifact.pipeline.named_steps["vectorizer"]
        transformed = vectorizer.transform([engineered])
        scores = artifact.pipeline.named_steps["model"].coef_[0] * transformed[0]
        names = vectorizer.get_feature_names_out()
        coefficient_top = [name for _, name in sorted(zip(np.abs(scores), names, strict=False), reverse=True)[:5]]
        output: dict[str, object] = {"coefficient_times_value": coefficient_top}
        try:
            shap_values = ShapService().explain(artifact.pipeline, [BENCHMARK_FEATURES])
            shap_top = [name for name, _ in sorted(shap_values.items(), key=lambda item: abs(item[1]), reverse=True)[:5]]
            output["shap"] = shap_top
        except ImportError:
            pass
        try:
            lime_values = LimeService().explain(artifact.pipeline, BENCHMARK_FEATURES)
            lime_top = [name for name, _ in sorted(lime_values.items(), key=lambda item: abs(item[1]), reverse=True)[:5]]
            output["lime"] = lime_top
        except ImportError:
            pass
        if "shap" in output and "lime" in output:
            names_union = sorted(set(output["shap"]) | set(output["lime"]))
            shap_ranks = [output["shap"].index(name) if name in output["shap"] else 5 for name in names_union]
            lime_ranks = [output["lime"].index(name) if name in output["lime"] else 5 for name in names_union]
            output["spearman_rank_agreement"] = float(spearmanr(shap_ranks, lime_ranks).statistic)
        return output


def _package_available(name: str) -> bool:
    try:
        importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return False
    return True


def main() -> None:
    frame = pd.read_csv(DATA_PATH)
    results = {
        "governance_cases": governance_results(),
        "detectors": detector_results(),
        "semantic_drift": {"legacy_all_pairs": detect_semantic_drift(["travel", "grocery"], ["travel", "grocery"]), "paired_best_match": detect_semantic_drift(["travel", "grocery"], ["travel", "grocery"], mode="paired_best_match")},
        "data_quality": {"legacy_none_only": DataQualityChecker(treat_nan_as_missing=False).evaluate(_records_without_nan(frame.head(1000).drop(columns=["isFraud"]))).score, "nan_as_missing": DataQualityChecker(treat_nan_as_missing=True).evaluate(frame.head(1000).drop(columns=["isFraud"]).to_dict("records")).score},
        "models": model_results(frame),
        "explainability": explainability_results(frame),
        "package_versions": {name: importlib.metadata.version(name) for name in ("numpy", "pandas", "scikit-learn", "shap", "lime") if _package_available(name)},
    }
    output = ROOT / "results"
    output.mkdir(exist_ok=True)
    (output / "experiment_results.json").write_text(json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = ["# Experiment Results", "", "Generated by `run_experiments.py`.", "", "## Package versions", "", "| Package | Version |", "| --- | --- |"]
    lines.extend(f"| {name} | {version} |" for name, version in results["package_versions"].items())
    lines.extend(["", "## Legacy vs new", "", "| Value | Legacy | New |", "| --- | --- | --- |"])
    lines.extend([
        f"| data quality score | {results['data_quality']['legacy_none_only']} | {results['data_quality']['nan_as_missing']} |",
        f"| semantic drift identical sets | {results['semantic_drift']['legacy_all_pairs']} | {results['semantic_drift']['paired_best_match']} |",
        f"| ROC-AUC | {results['models']['legacy']['roc_auc']} | {results['models']['scaled']['roc_auc']} |",
        f"| precision | {results['models']['legacy']['precision']} | {results['models']['scaled']['precision']} |",
        f"| recall | {results['models']['legacy']['recall']} | {results['models']['scaled']['recall']} |",
        f"| F1 | {results['models']['legacy']['f1']} | {results['models']['scaled']['f1']} |",
        f"| convergence warning | {results['models']['legacy']['convergence_warning']} | {results['models']['scaled']['convergence_warning']} |",
    ])
    (ROOT / "EXPERIMENT_RESULTS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\nLegacy vs new changed values")
    print("\n".join(lines[lines.index("| --- | --- | --- |") + 1:]))
    print(json.dumps(results, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()