from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import numpy as np

from backend.utils.helpers import stable_hash


def encode_categoricals(features: Mapping[str, Any], categorical_prefix: str = "cat_") -> dict[str, float]:
    encoded: dict[str, float] = {}
    for key, value in features.items():
        if isinstance(value, str):
            encoded[f"{categorical_prefix}{key}"] = float(stable_hash({key: value}) % 1000) / 1000.0
        elif isinstance(value, bool):
            encoded[key] = float(int(value))
        elif isinstance(value, (int, float, np.number)):
            encoded[key] = float(value)
    return encoded
