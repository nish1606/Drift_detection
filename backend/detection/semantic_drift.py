from __future__ import annotations

from collections.abc import Iterable

import numpy as np

SEMANTIC_DRIFT_THRESHOLD = 0.3


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


def detect_semantic_drift(reference_texts: Iterable[str], current_texts: Iterable[str], mode: str = "all_pairs") -> float:
    reference_texts = list(reference_texts)
    current_texts = list(current_texts)
    if not reference_texts or not current_texts:
        return 0.0
    if mode == "paired_best_match":
        similarities = [max(cosine_similarity(cur, ref) for ref in reference_texts) for cur in current_texts]
    elif mode == "all_pairs":
        similarities = [cosine_similarity(ref, cur) for ref in reference_texts for cur in current_texts]
    else:
        raise ValueError("mode must be 'all_pairs' or 'paired_best_match'")
    return float(1.0 - np.mean(similarities))


def is_semantic_drift(score: float, threshold: float = SEMANTIC_DRIFT_THRESHOLD) -> bool:
    return score >= threshold
