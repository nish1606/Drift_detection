from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import numpy as np


def _vectorize_text(value: str) -> np.ndarray:
    vector = np.zeros(26, dtype=float)
    for char in value.lower():
        if "a" <= char <= "z":
            vector[ord(char) - ord("a")] += 1.0
    norm = np.linalg.norm(vector)
    return vector / norm if norm else vector


def cosine_similarity(a: str, b: str) -> float:
    first = _vectorize_text(a)
    second = _vectorize_text(b)
    if not first.any() and not second.any():
        return 1.0
    return float(np.dot(first, second))


def detect_semantic_drift(reference_texts: Iterable[str], current_texts: Iterable[str]) -> float:
    reference_texts = list(reference_texts)
    current_texts = list(current_texts)
    if not reference_texts or not current_texts:
        return 0.0
    similarities = []
    for ref in reference_texts:
        for cur in current_texts:
            similarities.append(cosine_similarity(ref, cur))
    return float(1.0 - np.mean(similarities))
