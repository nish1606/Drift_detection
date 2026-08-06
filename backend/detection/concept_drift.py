from __future__ import annotations

from dataclasses import dataclass, field
from collections import deque
from typing import Deque


@dataclass
class ConceptDriftState:
    window: Deque[float] = field(default_factory=lambda: deque(maxlen=200))
    baseline_mean: float = 0.0
    baseline_initialized: bool = False


class ConceptDriftDetector:
    def __init__(self, threshold: float = 0.15, min_samples: int = 30) -> None:
        self.threshold = threshold
        self.min_samples = min_samples
        self.state = ConceptDriftState()

    def update(self, error_rate: float) -> bool:
        self.state.window.append(float(error_rate))
        if len(self.state.window) < self.min_samples:
            return False
        current_mean = sum(self.state.window) / len(self.state.window)
        if not self.state.baseline_initialized:
            self.state.baseline_mean = current_mean
            self.state.baseline_initialized = True
            return False
        drift = abs(current_mean - self.state.baseline_mean)
        if drift >= self.threshold:
            self.state.baseline_mean = current_mean
            return True
        return False
