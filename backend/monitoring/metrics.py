from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class MetricsCollector:
    counters: dict[str, float] = field(default_factory=dict)
    gauges: dict[str, float] = field(default_factory=dict)
    histograms: dict[str, list[float]] = field(default_factory=dict)

    def increment(self, metric: str, value: float = 1.0) -> None:
        self.counters[metric] = self.counters.get(metric, 0.0) + value

    def set_gauge(self, metric: str, value: float) -> None:
        self.gauges[metric] = value

    def observe(self, metric: str, value: float) -> None:
        self.histograms.setdefault(metric, []).append(value)

    def snapshot(self) -> dict[str, Any]:
        return {
            "counters": dict(self.counters),
            "gauges": dict(self.gauges),
            "histograms": {name: list(values) for name, values in self.histograms.items()},
        }

    def prometheus_text(self) -> str:
        lines: list[str] = []
        for name, value in self.counters.items():
            lines.append(f"{name} {value}")
        for name, value in self.gauges.items():
            lines.append(f"{name} {value}")
        for name, values in self.histograms.items():
            for value in values:
                lines.append(f"{name}_bucket {value}")
        return "\n".join(lines)
