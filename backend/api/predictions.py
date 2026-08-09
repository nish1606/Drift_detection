from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.core.auth import get_current_user
from backend.database import crud
from backend.database.postgres import get_db

router = APIRouter()


@router.get("/predictions")
def get_predictions(limit: int = 100, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    items = crud.list_predictions(db, limit=limit)
    results = []
    for i in items:
        explanations = i.explanations or {}
        if isinstance(explanations, dict) and "prediction" in explanations and isinstance(explanations["prediction"], dict):
            explanations = explanations["prediction"]
        results.append({
            "id": i.id,
            "request_id": i.request_id,
            "timestamp": i.created_at.isoformat(),
            "amount": i.raw_features.get("amount") if isinstance(i.raw_features, dict) else None,
            "confidence": i.probability,
            "prediction": i.prediction,
            "model_version": i.model_version,
            "raw_features": i.raw_features,
            "engineered_features": i.engineered_features,
            "explanations": explanations,
        })
    return results


@router.get("/predictions/{prediction_id}")
def get_prediction(prediction_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    item = crud.get_prediction_by_request_id(db, prediction_id)
    if not item:
        raise HTTPException(status_code=404, detail="Prediction not found")
    explanations = item.explanations or {}
    if isinstance(explanations, dict) and "prediction" in explanations and isinstance(explanations["prediction"], dict):
        explanations = explanations["prediction"]
    return {
        "id": item.id,
        "request_id": item.request_id,
        "timestamp": item.created_at.isoformat(),
        "amount": item.raw_features.get("amount") if isinstance(item.raw_features, dict) else None,
        "confidence": item.probability,
        "prediction": item.prediction,
        "model_version": item.model_version,
        "raw_features": item.raw_features,
        "engineered_features": item.engineered_features,
        "explanations": explanations,
    }
