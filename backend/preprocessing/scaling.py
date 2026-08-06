from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass
class FeatureScaler:
    means: dict[str, float] = field(default_factory=dict)
    stds: dict[str, float] = field(default_factory=dict)

    def fit(self, records: list[dict[str, float]]) -> "FeatureScaler":
        if not records:
            return self
        keys = sorted({key for record in records for key in record})
        for key in keys:
            values = np.asarray([record.get(key, 0.0) for record in records], dtype=float)
            self.means[key] = float(np.mean(values))
            std = float(np.std(values))
            self.stds[key] = std if std > 0 else 1.0
        return self

    def transform(self, record: dict[str, float]) -> dict[str, float]:
        transformed: dict[str, float] = {}
        for key, value in record.items():
            mean = self.means.get(key, 0.0)
            std = self.stds.get(key, 1.0)
            transformed[key] = float((float(value) - mean) / std)
        return transformed

    def fit_transform(self, records: list[dict[str, float]]) -> list[dict[str, float]]:
        self.fit(records)
        return [self.transform(record) for record in records]
