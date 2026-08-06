from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from backend.api.deps import db_dep
from backend.database.models import PredictionRecord
from backend.schemas.prediction import PredictionRequest, PredictionResponse

router = APIRouter(tags=["transactions"])


@router.get("/transactions")
def list_transactions(session: Session = Depends(db_dep), limit: int = 50) -> list[dict[str, object]]:
    rows = session.scalars(select(PredictionRecord).order_by(PredictionRecord.created_at.desc()).limit(limit)).all()
    return [
        {
            "id": row.request_id,
            "amount": row.raw_features.get("amount", 0),
            "timestamp": row.created_at.isoformat(),
            "confidence": row.probability,
            "features": row.raw_features,
            "modelVersion": row.model_version,
            "prediction": "Fraud" if row.prediction == 1 else "Legitimate",
            "reason": f"Model decision: {row.decision}",
            "status": "Pending",
            "shapValues": row.explanations.get("prediction", {}).get("top_features", [])[:5],
            "topFactor": (row.explanations.get("prediction", {}).get("top_features", [[None, 0]])[0] or [None])[0] or "unknown",
        }
        for row in rows
    ]


@router.post("/transactions/{request_id}/status")
def update_status(request_id: str, status: str, session: Session = Depends(db_dep)) -> dict[str, object]:
    stmt = update(PredictionRecord).where(PredictionRecord.request_id == request_id).values(raw_features={"status": status})
    session.execute(stmt)
    session.commit()
    return {"request_id": request_id, "status": status}
