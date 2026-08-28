from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import Any

import numpy as np

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
EPSILON = 1e-6


def dataset_path(name: str) -> Path | None:
    candidate = (DATA_DIR / name).resolve()
    try:
        candidate.relative_to(DATA_DIR.resolve())
    except ValueError:
        return None
    return candidate if candidate.is_file() and candidate.suffix.casefold() == ".csv" else None


def discover_datasets() -> dict[str, Path]:
    return {path.relative_to(DATA_DIR).as_posix(): path for path in DATA_DIR.rglob("*.csv") if path.is_file()}


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return reader.fieldnames or [], list(reader)


def _number(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _is_numeric(rows: list[dict[str, str]], field: str) -> bool:
    values = [_number(row.get(field)) for row in rows]
    return bool(values) and any(value is not None for value in values) and all(
        value is not None or not row.get(field, "").strip() for value, row in zip(values, rows)
    )


def dataset_metadata(path: Path) -> dict[str, object]:
    fields, rows = _read_csv(path)
    numeric = [field for field in fields if _is_numeric(rows, field)]
    categorical = [field for field in fields if field not in numeric]
    return {"name": path.relative_to(DATA_DIR).as_posix(), "rows": len(rows), "features": numeric, "numericFeatures": numeric, "categoricalFeatures": categorical}


def _psi(reference: np.ndarray, current: np.ndarray, bins: int = 10) -> tuple[float, list[dict[str, object]]]:
    if reference.size == 0 or current.size == 0:
        return 0.0, []
    minimum = min(float(reference.min()), float(current.min()))
    maximum = max(float(reference.max()), float(current.max()))
    edges = np.linspace(minimum, maximum, bins + 1)
    if np.allclose(edges[0], edges[-1]):
        edges = np.arange(bins + 1, dtype=float) - bins / 2 + edges[0]
    reference_counts, _ = np.histogram(reference, bins=edges)
    current_counts, _ = np.histogram(current, bins=edges)
    reference_share = reference_counts / max(reference_counts.sum(), 1)
    current_share = current_counts / max(current_counts.sum(), 1)
    score = float(np.sum((current_share - reference_share) * np.log((current_share + EPSILON) / (reference_share + EPSILON))))
    bins_result = [{"bin": index, "label": f"{edges[index]:.0f}-{edges[index + 1]:.0f}", "reference": int(reference_counts[index]), "current": int(current_counts[index])} for index in range(bins)]
    return max(0.0, score), bins_result


def _categorical_psi(reference: list[str], current: list[str]) -> float:
    categories = sorted(set(reference) | set(current))
    score = 0.0
    for category in categories:
        reference_share = reference.count(category) / max(len(reference), 1)
        current_share = current.count(category) / max(len(current), 1)
        score += (current_share - reference_share) * math.log((current_share + EPSILON) / (reference_share + EPSILON))
    return max(0.0, float(score))


def _status(score: float) -> str:
    return "high" if score >= 0.2 else "watch" if score >= 0.1 else "normal"


def compare_datasets(reference: Path, current: Path, requested_features: list[str] | None = None) -> dict[str, object]:
    reference_fields, reference_rows = _read_csv(reference)
    current_fields, current_rows = _read_csv(current)
    current_by_lower = {field.casefold(): field for field in current_fields}
    shared = [field for field in reference_fields if field.casefold() in current_by_lower]
    numeric_features = [field for field in shared if _is_numeric(reference_rows, field) and _is_numeric(current_rows, current_by_lower[field.casefold()])]
    categorical_features = [field for field in shared if field not in numeric_features]
    if requested_features:
        requested = {feature.casefold() for feature in requested_features}
        numeric_features = [field for field in numeric_features if field.casefold() in requested]
        categorical_features = [field for field in categorical_features if field.casefold() in requested]
    results: list[dict[str, object]] = []
    for field in numeric_features:
        current_field = current_by_lower[field.casefold()]
        ref_values = np.asarray([value for row in reference_rows if (value := _number(row.get(field))) is not None], dtype=float)
        cur_values = np.asarray([value for row in current_rows if (value := _number(row.get(current_field))) is not None], dtype=float)
        score, bins = _psi(ref_values, cur_values)
        results.append({"feature": field, "type": "numeric", "driftScore": round(score, 4), "status": _status(score), "referenceRows": len(ref_values), "currentRows": len(cur_values), "referenceMean": round(float(ref_values.mean()), 3) if ref_values.size else None, "currentMean": round(float(cur_values.mean()), 3) if cur_values.size else None, "referenceMissingPct": round((len(reference_rows) - len(ref_values)) / max(len(reference_rows), 1) * 100, 2), "currentMissingPct": round((len(current_rows) - len(cur_values)) / max(len(current_rows), 1) * 100, 2), "bins": bins})
    for field in categorical_features:
        current_field = current_by_lower[field.casefold()]
        ref_values = [row.get(field, "").strip() for row in reference_rows]
        cur_values = [row.get(current_field, "").strip() for row in current_rows]
        ref_present = [value for value in ref_values if value]
        cur_present = [value for value in cur_values if value]
        score = _categorical_psi(ref_present, cur_present)
        results.append({"feature": field, "type": "categorical", "driftScore": round(score, 4), "status": _status(score), "referenceRows": len(ref_present), "currentRows": len(cur_present), "referenceMean": None, "currentMean": None, "referenceMissingPct": round((len(ref_values) - len(ref_present)) / max(len(ref_values), 1) * 100, 2), "currentMissingPct": round((len(cur_values) - len(cur_present)) / max(len(cur_values), 1) * 100, 2), "bins": []})
    overall = float(np.mean([item["driftScore"] for item in results])) if results else 0.0
    return {"features": results, "overallScore": round(overall, 4), "overallStatus": _status(overall), "sharedFeatures": [item["feature"] for item in results]}