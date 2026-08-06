from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from backend.utils.helpers import ensure_float


def clean_features(raw_features: Mapping[str, Any]) -> dict[str, Any]:
    cleaned: dict[str, Any] = {}
    for key, value in raw_features.items():
        if value is None:
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
