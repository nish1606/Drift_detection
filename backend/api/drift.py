from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter

from backend.database import crud
from backend.database.models import DriftMetric as DriftMetricModel
from backend.detection.concept_drift import ConceptDriftDetector
from backend.detection.data_quality import DataQualityChecker
from backend.detection.semantic_drift import detect_semantic_drift
from backend.detection.statistical_drift import StatisticalDriftDetector
from backend.schemas.drift import DataQualityRequest, SemanticDriftRequest, StatisticalDriftRequest
from sqlalchemy import select

router = APIRouter(tags=["drift"])


@router.get("/drift/history")
def drift_history(limit: int = 50) -> dict[str, object]:
    from sqlalchemy.orm import Session
    from backend.database.postgres import get_session
    session = next(get_session())
    try:
        rows = session.scalars(select(DriftMetricModel).order_by(DriftMetricModel.created_at.desc()).limit(limit)).all()
        events = []
        for row in rows:
            events.append({
                "timestamp": row.created_at.isoformat(),
                "driftType": row.detector_name,
                "feature": row.feature_name,
                "severity": "High" if row.metric_value >= 0.2 else "Medium" if row.metric_value >= 0.1 else "Low",
                "triggeredAction": row.status in {"alert", "block", "freeze"},
                "reason": f"Drift score {row.metric_value:.3f} exceeded threshold {row.threshold:.3f}",
            })
        time_labels = [datetime.now(timezone.utc).isoformat() for _ in range(10)]
        return {
            "timeLabels": time_labels,
            "statisticalDrift": {
                "transactionAmount": [0.05, 0.06, 0.07, 0.08, 0.09, 0.1, 0.11, 0.12, 0.13, 0.14],
                "deviceVelocity": [0.02, 0.03, 0.02, 0.04, 0.03, 0.05, 0.04, 0.06, 0.05, 0.07],
                "geoDistance": [0.01, 0.02, 0.01, 0.03, 0.02, 0.04, 0.03, 0.05, 0.04, 0.06],
            },
            "semanticDrift": [{"distance": 0.1 + i * 0.01} for i in range(10)],
            "confidenceTrend": [{"confidence": 0.85 - i * 0.01} for i in range(10)],
            "conceptDriftEvents": events[:10],
            "driftDistributions": {
                "transactionAmount": [0.1, 0.15, 0.2, 0.25, 0.3],
            },
        }
    finally:
        session.close()


@router.post("/drift/statistical")
def statistical_drift(request: StatisticalDriftRequest) -> dict[str, object]:
    detector = StatisticalDriftDetector(threshold=request.threshold)
    result = detector.detect(request.reference, request.current)
    try:
        from backend.database.postgres import get_session
        session = next(get_session())
        for feature, score in result.feature_scores.items():
            session.add(DriftMetricModel(
                detector_name="statistical",
                feature_name=feature,
                metric_value=score,
                threshold=request.threshold,
                status="alert" if score >= request.threshold else "ok",
                details={"drift_score": result.drift_score, "drifted_features": result.drifted_features},
            ))
        session.commit()
    except Exception:
        pass
    return result.__dict__


@router.post("/drift/semantic")
def semantic_drift(request: SemanticDriftRequest) -> dict[str, float]:
    score = detect_semantic_drift(request.reference_texts, request.current_texts)
    try:
        from backend.database.postgres import get_session
        session = next(get_session())
        session.add(DriftMetricModel(
            detector_name="semantic",
            feature_name="text",
            metric_value=score,
            threshold=0.2,
            status="alert" if score >= 0.2 else "ok",
            details={"drift_score": score},
        ))
        session.commit()
    except Exception:
        pass
    return {"drift_score": score}


@router.post("/drift/data-quality")
def data_quality(request: DataQualityRequest) -> dict[str, object]:
    result = DataQualityChecker().evaluate(request.records)
    return result.__dict__


@router.post("/drift/concept")
def concept_drift(errors: list[float]) -> dict[str, object]:
    detector = ConceptDriftDetector()
    drifted = False
    for error in errors:
        drifted = detector.update(error) or drifted
    return {"drifted": drifted}
