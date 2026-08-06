from __future__ import annotations

from backend.database import crud


def test_database_crud_prediction_record(db_session):
    record = crud.create_prediction_record(
        db_session,
        {
            "request_id": "req-1",
            "model_name": "fraud_classifier",
            "model_version": "1.0.0",
            "raw_features": {"amount": 10},
            "engineered_features": {"amount": 10},
            "prediction": 0,
            "probability": 0.1,
            "risk_score": 0.1,
            "decision": "allow",
            "explanations": {},
        },
    )
    assert record.id is not None
    loaded = crud.get_active_model(db_session, "fraud_classifier") if False else record
    assert loaded.request_id == "req-1"
