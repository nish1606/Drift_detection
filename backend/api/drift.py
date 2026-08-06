from __future__ import annotations

from fastapi import APIRouter

from backend.detection.concept_drift import ConceptDriftDetector
from backend.detection.data_quality import DataQualityChecker
from backend.detection.semantic_drift import detect_semantic_drift
from backend.detection.statistical_drift import StatisticalDriftDetector
from backend.schemas.drift import DataQualityRequest, SemanticDriftRequest, StatisticalDriftRequest

router = APIRouter(tags=["drift"])


@router.post("/drift/statistical")
def statistical_drift(request: StatisticalDriftRequest) -> dict[str, object]:
    detector = StatisticalDriftDetector(threshold=request.threshold)
    result = detector.detect(request.reference, request.current)
    return result.__dict__


@router.post("/drift/semantic")
def semantic_drift(request: SemanticDriftRequest) -> dict[str, float]:
    return {"drift_score": detect_semantic_drift(request.reference_texts, request.current_texts)}


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
