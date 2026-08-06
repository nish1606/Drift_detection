from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass
class DataQualityResult:
    score: float
    issues: list[str] = field(default_factory=list)
    feature_scores: dict[str, float] = field(default_factory=dict)


class DataQualityChecker:
    def __init__(self, missing_threshold: float = 0.2, outlier_zscore: float = 3.0) -> None:
        self.missing_threshold = missing_threshold
        self.outlier_zscore = outlier_zscore

    def evaluate(self, records: list[Mapping[str, Any]]) -> DataQualityResult:
        if not records:
            return DataQualityResult(score=0.0, issues=["empty_dataset"])
        feature_scores: dict[str, float] = {}
        issues: list[str] = []
        keys = sorted({key for record in records for key in record})
        for key in keys:
            values = [record.get(key) for record in records]
            missing_rate = sum(value is None for value in values) / len(values)
            score = max(0.0, 1.0 - missing_rate)
            if missing_rate >= self.missing_threshold:
                issues.append(f"high_missingness:{key}")
            numeric_values = np.asarray([float(value) for value in values if isinstance(value, (int, float))], dtype=float)
            if numeric_values.size > 1:
                mean = float(np.mean(numeric_values))
                std = float(np.std(numeric_values)) or 1.0
                zscores = np.abs((numeric_values - mean) / std)
                if np.max(zscores) >= self.outlier_zscore:
                    issues.append(f"outlier_detected:{key}")
                    score *= 0.9
            feature_scores[key] = score
        overall = float(np.mean(list(feature_scores.values()))) if feature_scores else 0.0
        return DataQualityResult(score=overall, issues=issues, feature_scores=feature_scores)
