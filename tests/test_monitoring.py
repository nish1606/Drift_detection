from __future__ import annotations

from backend.monitoring.audit import AuditService
from backend.monitoring.exporters import export_audit_json, export_metrics_json
from backend.monitoring.metrics import MetricsCollector


def test_monitoring_collector_and_exporters(tmp_path, db_session):
    collector = MetricsCollector()
    collector.increment("predictions_total")
    collector.observe("latency_seconds", 0.25)
    metrics_path = export_metrics_json(collector, str(tmp_path / "metrics.json"))
    assert metrics_path.endswith("metrics.json")
    audit = AuditService(db_session)
    audit.record(actor="system", action="test", resource_type="model", resource_id="1", status="ok", metadata={})
    records = audit.latest(10)
    audit_path = export_audit_json(records, str(tmp_path / "audit.json"))
    assert audit_path.endswith("audit.json")
