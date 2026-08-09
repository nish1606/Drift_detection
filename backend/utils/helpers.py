from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Sequence
from datetime import UTC, datetime
from typing import Any

import numpy as np


def utcnow() -> datetime:
    return datetime.now(UTC)


def stable_hash(value: Any) -> int:
    payload = json.dumps(value, sort_keys=True, default=str).encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()
    return int(digest[:12], 16)


def ensure_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_mean(values: Sequence[float] | np.ndarray) -> float:
    array = np.asarray(values, dtype=float)
    if array.size == 0:
        return 0.0
    return float(np.nanmean(array))


def flatten(nested: Iterable[Iterable[Any]]) -> list[Any]:
    flattened: list[Any] = []
    for chunk in nested:
        flattened.extend(chunk)
    return flattened
