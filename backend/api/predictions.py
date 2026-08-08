from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import crud
from backend.database.session import get_db
from backend.api.deps import get_current_user

router = APIRouter()


@router.get("/predictions")
def get_predictions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    items = crud.get_predictions(db, skip=skip, limit=limit)
    return [{"id": i.id, "timestamp": i.timestamp.isoformat(), "amount": i.amount, "confidence": i.confidence, "prediction": i.prediction, "model_version": i.model_version} for i in items]


@router.get("/predictions/{prediction_id}")
def get_prediction(prediction_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    item = crud.get_prediction(db, prediction_id)
    if not item:
        raise HTTPException(status_code=404, detail="Prediction not found")
    return {"id": item.id, "timestamp": item.timestamp.isoformat(), "amount": item.amount, "confidence": item.confidence, "prediction": item.prediction, "model_version": item.model_version}
