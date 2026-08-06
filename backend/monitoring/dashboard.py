from __future__ import annotations

from typing import Any

from backend.monitoring.metrics import MetricsCollector


class MonitoringDashboard:
    def __init__(self, collector: MetricsCollector | None = None) -> None:
        self.collector = collector or MetricsCollector()

    def build(self, *, recent_alerts: list[dict[str, Any]], drift_summary: dict[str, Any], audit_summary: dict[str, Any]) -> dict[str, Any]:
        return {
            "metrics": self.collector.snapshot(),
            "recent_alerts": recent_alerts,
            "drift_summary": drift_summary,
            "audit_summary": audit_summary,
        }
