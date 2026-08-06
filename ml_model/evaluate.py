from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score

from backend.utils.helpers import safe_mean


@dataclass
class EvaluationResult:
    accuracy: float
    precision: float
    recall: float
    f1: float
    roc_auc: float
    confusion: dict[str, int]
    threshold: float

    def as_dict(self) -> dict[str, float | dict[str, int]]:
        return {
            "accuracy": self.accuracy,
            "precision": self.precision,
            "recall": self.recall,
            "f1": self.f1,
            "roc_auc": self.roc_auc,
            "confusion": self.confusion,
            "threshold": self.threshold,
        }


def evaluate_predictions(y_true: list[int], y_prob: list[float], threshold: float = 0.5) -> EvaluationResult:
    if not y_true:
        raise ValueError("y_true cannot be empty")
    probabilities = np.asarray(y_prob, dtype=float)
    labels = np.asarray(y_true, dtype=int)
    predicted = (probabilities >= threshold).astype(int)
    accuracy = float(accuracy_score(labels, predicted))
    precision = float(precision_score(labels, predicted, zero_division=0))
    recall = float(recall_score(labels, predicted, zero_division=0))
    f1 = float(f1_score(labels, predicted, zero_division=0))
    if len(set(labels.tolist())) > 1:
        roc_auc = float(roc_auc_score(labels, probabilities))
    else:
        roc_auc = 0.5
    matrix = confusion_matrix(labels, predicted, labels=[0, 1])
    confusion = {
        "tn": int(matrix[0, 0]),
        "fp": int(matrix[0, 1]),
        "fn": int(matrix[1, 0]),
        "tp": int(matrix[1, 1]),
    }
    return EvaluationResult(accuracy, precision, recall, f1, roc_auc, confusion, threshold)
