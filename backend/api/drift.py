from __future__ import annotations

import csv
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import joblib
import numpy as np
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from backend.api.deps import db_dep
from backend.core.auth import get_current_active_user
from backend.database import crud
from backend.database.models import User
from backend.detection.concept_drift import ConceptDriftDetector
from backend.detection.dataset_comparison import compare_datasets as compare_dataset_files
from backend.detection.dataset_comparison import dataset_metadata, dataset_path, discover_datasets
from backend.detection.data_quality import DataQualityChecker
from backend.detection.semantic_drift import detect_semantic_drift
from backend.detection.statistical_drift import StatisticalDriftDetector
from backend.schemas.drift import (
    DataQualityRequest,
    SemanticDriftRequest,
    StatisticalDriftRequest,
)

router = APIRouter(tags=["drift"])

ARTIFACT_DIR = Path(__file__).resolve().parent.parent.parent / "ml_model" / "artifacts"
BASELINE_STATS_PATH = ARTIFACT_DIR / "baseline_stats.pkl"
_REFERENCE_CACHE: dict[str, np.ndarray] = {}
DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class DatasetComparisonRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reference: str
    current: str
    #: Single feature, kept for backwards compatibility; prefer ``features``.
    feature: str | None = None
    #: Features to compare. Omit (or pass an empty list) to compare every
    #: feature the two datasets share.
    features: list[str] = Field(default_factory=list, max_length=200)


def _dataset_paths() -> dict[str, Path]:
    return discover_datasets()


def _read_numeric_values(path: Path, feature: str) -> list[float]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        field = next((name for name in (reader.fieldnames or []) if name.lower() == feature.lower()), None)
        if field is None:
            return []
        values = []
        for row in reader:
            try:
                value = float(row.get(field, ""))
            except (TypeError, ValueError):
                continue
            if np.isfinite(value):
                values.append(value)
        return values


def _distribution(values: list[float], edges: np.ndarray) -> list[int]:
    counts, _ = np.histogram(values, bins=edges)
    return counts.astype(int).tolist()


@router.get("/datasets")
def list_datasets(user: User = Depends(get_current_active_user)) -> list[dict[str, object]]:
    return [dataset_metadata(path) for _, path in sorted(_dataset_paths().items())]


@router.post("/datasets/compare")
def compare_datasets(request: DatasetComparisonRequest, user: User = Depends(get_current_active_user)) -> dict[str, object]:
    reference_path = dataset_path(request.reference)
    current_path = dataset_path(request.current)
    if reference_path is None or current_path is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    requested = [feature for feature in request.features if feature]
    if request.feature:
        requested.append(request.feature)
    result = compare_dataset_files(reference_path, current_path, requested or None)
    features = result["features"]
    if not features:
        wanted = ", ".join(requested) if requested else "any shared feature"
        raise HTTPException(status_code=400, detail=f"No comparable values for {wanted}")
    payload = {
        "reference": request.reference,
        "current": request.current,
        "requestedFeatures": requested or None,
        "features": features,
        "featureCount": len(features),
        "overallScore": result["overallScore"],
        "overallStatus": result["overallStatus"],
        "sharedFeatures": result["sharedFeatures"],
    }
    # Preserve the single-feature response shape so existing callers keep working.
    if len(features) == 1:
        selected = features[0]
        payload.update(
            {
                "feature": selected["feature"],
                "referenceRows": selected["referenceRows"],
                "currentRows": selected["currentRows"],
                "referenceMean": selected["referenceMean"],
                "currentMean": selected["currentMean"],
                "driftScore": selected["driftScore"],
                "bins": selected["bins"],
            }
        )
    return payload


@router.post("/datasets/upload")
async def upload_dataset(file: UploadFile = File(...), user: User = Depends(get_current_active_user)) -> dict[str, object]:
    original_name = Path(file.filename or "").name
    if not original_name or Path(original_name).suffix.casefold() != ".csv" or original_name != (file.filename or ""):
        raise HTTPException(status_code=400, detail="Only safe .csv filenames are accepted")
    content = await file.read(10 * 1024 * 1024 + 1)
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="CSV file exceeds the 10 MB limit")
    if file.content_type not in {"text/csv", "application/csv", "application/vnd.ms-excel", "application/octet-stream"}:
        raise HTTPException(status_code=415, detail="Upload must have a CSV content type")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    target = DATA_DIR / f"upload_{uuid4().hex}_{original_name}"
    target.write_bytes(content)
    try:
        metadata = dataset_metadata(target)
    except (UnicodeDecodeError, csv.Error) as error:
        target.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="Uploaded file is not a readable CSV") from error
    return metadata


def _load_baseline() -> dict[str, dict[str, float]] | None:
    if BASELINE_STATS_PATH.exists():
        try:
            return joblib.load(BASELINE_STATS_PATH)
        except Exception:
            return None
    return None


def _get_reference(feature: str, baseline: dict[str, dict[str, float]] | None, size: int = 500) -> np.ndarray:
    key = f"{feature}:{size}"
    if key in _REFERENCE_CACHE:
        return _REFERENCE_CACHE[key]
    stats = (baseline or {}).get(feature)
    if stats:
        rng = np.random.default_rng(42)
        reference = rng.normal(stats.get("mean", 0.0), max(stats.get("std", 1.0), 1e-6), size=size)
        _REFERENCE_CACHE[key] = reference
        return reference
    return np.array([])


def _compute_drift_for_feature(values: list[float], baseline: dict[str, dict[str, float]] | None, feature: str) -> float:
    if not values or not baseline:
        return 0.0
    stats = baseline.get(feature)
    if not stats:
        return 0.0
    live_mean = sum(values) / len(values)
    live_std = (sum((x - live_mean) ** 2 for x in values) / len(values)) ** 0.5
    mean_diff = abs(live_mean - stats.get("mean", 0.0)) / (stats.get("std", 1.0) + 1e-6)
    std_ratio = live_std / (stats.get("std", 1.0) + 1e-6) if stats.get("std", 1.0) > 1e-6 else 0.0
    drift = mean_diff * 0.1 + abs(std_ratio - 1.0) * 0.2
    return round(min(0.3, max(0.0, drift)), 4)


@router.post("/drift/statistical")
def statistical_drift(request: StatisticalDriftRequest, user: User = Depends(get_current_active_user)) -> dict[str, object]:
    detector = StatisticalDriftDetector(threshold=request.threshold)
    result = detector.detect(request.reference, request.current)
    return result.__dict__


@router.post("/drift/semantic")
def semantic_drift(request: SemanticDriftRequest, user: User = Depends(get_current_active_user)) -> dict[str, float]:
    return {"drift_score": detect_semantic_drift(request.reference_texts, request.current_texts, mode=request.mode)}


@router.post("/drift/data-quality")
def data_quality(request: DataQualityRequest, user: User = Depends(get_current_active_user)) -> dict[str, object]:
    result = DataQualityChecker().evaluate(request.records)
    return result.__dict__


@router.post("/drift/concept")
def concept_drift(errors: list[float], user: User = Depends(get_current_active_user)) -> dict[str, object]:
    detector = ConceptDriftDetector()
    drifted = False
    for error in errors:
        drifted = detector.update(error) or drifted
    return {"drifted": drifted}


@router.get("/summary")
def drift_summary(session: Session = Depends(db_dep), user: User = Depends(get_current_active_user)) -> dict[str, object]:
    baseline = _load_baseline() or {}
    recent_predictions = crud.list_predictions(session, limit=200)

    now = datetime.now(UTC)
    time_labels = [(now - timedelta(minutes=(len(recent_predictions) - 1 - i))).isoformat() for i in range(len(recent_predictions))]

    amounts = [float(p.raw_features.get("amount", 0)) for p in recent_predictions if p is not None and isinstance(p.raw_features, dict)]
    velocities = [float(p.raw_features.get("velocity_1h", 0)) for p in recent_predictions if p is not None and isinstance(p.raw_features, dict)]
    geos = [float(p.raw_features.get("geo_distance", 0)) for p in recent_predictions if p is not None and isinstance(p.raw_features, dict)]

    statistical_drift = {
        "transactionAmount": [_compute_drift_for_feature(amounts[: i + 1], baseline, "amount") for i in range(len(amounts))] or [0.0],
        "deviceVelocity": [_compute_drift_for_feature(velocities[: i + 1], baseline, "velocity_1h") for i in range(len(velocities))] or [0.0],
        "geoDistance": [_compute_drift_for_feature(geos[: i + 1], baseline, "geo_distance") for i in range(len(geos))] or [0.0],
    }

    confidence_trend = []
    for prediction in recent_predictions:
        confidence_trend.append({
            "timestamp": prediction.created_at.isoformat() if prediction.created_at else now.isoformat(),
            "confidence": float(prediction.probability),
        })
    if not confidence_trend:
        confidence_trend.append({"timestamp": now.isoformat(), "confidence": 0.0})

    concept_events = []
    if len(recent_predictions) >= 10:
        first_mean = sum(float(p.raw_features.get("amount", 0)) for p in recent_predictions[:10]) / 10
        for i in range(10, len(recent_predictions), 10):
            chunk = recent_predictions[i:i + 10]
            if not chunk:
                continue
            chunk_mean = sum(float(p.raw_features.get("amount", 0)) for p in chunk) / len(chunk)
            if abs(chunk_mean - first_mean) >= 50:
                concept_events.append({
                    "timestamp": chunk[0].created_at.isoformat() if chunk[0].created_at else now.isoformat(),
                    "feature": "transactionAmount",
                    "severity": "High" if abs(chunk_mean - first_mean) >= 150 else "Medium",
                    "reason": f"Mean transaction amount shifted by ${abs(chunk_mean - first_mean):.0f} from baseline ${first_mean:.0f}",
                    "driftType": "Concept drift",
                    "triggeredAction": abs(chunk_mean - first_mean) >= 150,
                })
                first_mean = chunk_mean

    semantic_drift = []
    if len(recent_predictions) >= 10:
        reference_texts = [p.raw_features.get("merchant_category", "unknown") for p in recent_predictions[:10] if isinstance(p.raw_features, dict)]
        for i in range(10, len(recent_predictions), 10):
            chunk = recent_predictions[i:i + 10]
            if not chunk:
                continue
            current_texts = [p.raw_features.get("merchant_category", "unknown") for p in chunk if isinstance(p.raw_features, dict)]
            if reference_texts and current_texts:
                distance = detect_semantic_drift(reference_texts, current_texts)
                semantic_drift.append({
                    "timestamp": chunk[0].created_at.isoformat() if chunk[0].created_at else now.isoformat(),
                    "distance": round(distance, 4),
                })

    return {
        "timeLabels": time_labels,
        "statisticalDrift": statistical_drift,
        "semanticDrift": semantic_drift,
        "confidenceTrend": confidence_trend,
        "conceptDriftEvents": concept_events,
        "driftDistributions": {
            "transactionAmount": [],
            "deviceVelocity": [],
            "geoDistance": [],
        },
    }