from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

from backend.utils.helpers import ensure_float


def _is_missing(value: Any) -> bool:
    """A value counts as missing when it is ``None`` or a float NaN."""
    return value is None or (isinstance(value, float) and math.isnan(value))


def clean_features(raw_features: Mapping[str, Any]) -> dict[str, Any]:
    cleaned: dict[str, Any] = {}
    for key, value in raw_features.items():
        if _is_missing(value):
            continue
        if isinstance(value, bool):
            cleaned[key] = int(value)
        elif isinstance(value, (int, float)):
            cleaned[key] = float(value)
        elif isinstance(value, str):
            stripped = value.strip()
            if stripped.replace(".", "", 1).replace("-", "", 1).isdigit():
                cleaned[key] = ensure_float(stripped)
            else:
                cleaned[key] = stripped
        else:
            cleaned[key] = value
    return cleaned
