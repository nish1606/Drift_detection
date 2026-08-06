from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass
class DriftResult:
    drift_score: float
    drifted_features: list[str] = field(default_factory=list)
    feature_scores: dict[str, float] = field(default_factory=dict)


class StatisticalDriftDetector:
    def __init__(self, threshold: float = 0.2, bins: int = 10) -> None:
        self.threshold = threshold
        self.bins = bins

    def _psi(self, reference: np.ndarray, current: np.ndarray) -> float:
        reference = np.asarray(reference, dtype=float)
        current = np.asarray(current, dtype=float)
        if reference.size == 0 or current.size == 0:
            return 0.0
        quantiles = np.unique(np.quantile(reference, np.linspace(0, 1, self.bins + 1)))
        if quantiles.size < 3:
            quantiles = np.linspace(min(reference.min(), current.min()), max(reference.max(), current.max()), self.bins + 1)
        ref_hist, edges = np.histogram(reference, bins=quantiles)
        cur_hist, _ = np.histogram(current, bins=edges)
        ref_pct = ref_hist / max(ref_hist.sum(), 1)
        cur_pct = cur_hist / max(cur_hist.sum(), 1)
        ref_pct = np.where(ref_pct == 0, 1e-6, ref_pct)
        cur_pct = np.where(cur_pct == 0, 1e-6, cur_pct)
        return float(np.sum((cur_pct - ref_pct) * np.log(cur_pct / ref_pct)))

    def detect(self, reference: dict[str, list[float]], current: dict[str, list[float]]) -> DriftResult:
        scores: dict[str, float] = {}
        drifted: list[str] = []
        for feature, ref_values in reference.items():
            cur_values = current.get(feature, [])
            score = self._psi(np.asarray(ref_values, dtype=float), np.asarray(cur_values, dtype=float))
            scores[feature] = score
            if score >= self.threshold:
                drifted.append(feature)
        overall = float(np.mean(list(scores.values()))) if scores else 0.0
        return DriftResult(drift_score=overall, drifted_features=drifted, feature_scores=scores)
