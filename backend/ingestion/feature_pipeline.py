from __future__ import annotations

from typing import Any

from backend.preprocessing.feature_engineering import FeatureEngineer


class FeaturePipeline:
    def __init__(self) -> None:
        self.engineer = FeatureEngineer()

    def process(self, payload: dict[str, Any]) -> dict[str, float]:
        return self.engineer.build(payload)
