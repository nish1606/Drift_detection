from __future__ import annotations

from backend.database import crud
from backend.response.alerting import AlertingService
from backend.response.freeze import FreezeService
from backend.response.retraining import RetrainingService
from backend.response.review_queue import ReviewQueueService


def test_response_workflows(db_session):
    crud.create_model_artifact(
        db_session,
        {
            "name": "fraud_classifier",
            "version": "1.0",
            "uri": "./artifact.joblib",
            "status": "active",
            "metrics": {},
            "schema": {},
            "active": True,
        },
    )
    alert = AlertingService(db_session).create_alert(severity="medium", message="review needed", alert_type="manual_review")
    assert alert.id is not None
    queue = ReviewQueueService(db_session).enqueue(message="manual review needed")
    assert queue["status"] == "queued"
    retraining = RetrainingService(db_session).enqueue(model_name="fraud_classifier", trigger_reason="drift")
    assert retraining.id is not None
    frozen = FreezeService(db_session).freeze_model("fraud_classifier")
    assert frozen.status == "frozen"
