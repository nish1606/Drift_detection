from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from backend.monitoring.metrics import MetricsCollector


def export_metrics_json(collector: MetricsCollector, path: str) -> str:
    output_path = Path(path)
    output_path.write_text(json.dumps(collector.snapshot(), indent=2), encoding="utf-8")
    return str(output_path)


def export_audit_json(records: list[dict[str, Any]], path: str) -> str:
    output_path = Path(path)
    output_path.write_text(json.dumps(records, indent=2), encoding="utf-8")
    return str(output_path)
