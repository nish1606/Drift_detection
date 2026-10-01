from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends

from backend.api.deps import (
    decision_engine_dep,
    model_service_dep,
    policy_engine_dep,
    risk_scorer_dep,
)
from backend.core.auth import get_current_active_user
from backend.database import crud
from backend.database.models import User
from backend.database.postgres import get_session
from backend.governance.decision_engine import DecisionEngine
from backend.governance.policy_engine import PolicyEngine
from backend.governance.risk_scoring import RiskScorer
from backend.logging.decision_logger import DecisionLogger
from backend.response.alerting import AlertingService
from backend.schemas.prediction import PredictionRequest, PredictionResponse

router = APIRouter(tags=["prediction"])


def _create_alert(
    request_id: str,
    request: PredictionRequest,
    prediction_result: object,
    score: dict[str, object],
    decision_str: str,
) -> list[dict[str, object]]:
    """Create the decision alert in the request path so it can be returned inline."""
    if decision_str not in {"block", "freeze", "review"}:
        return []
    severity = "high" if decision_str in {"block", "freeze"} else "medium"
    session = get_session()
    try:
        alert = AlertingService(session).create_alert(
            severity=severity,
            message=f"Prediction {decision_str} for {request.model_name}",
            alert_type="prediction_decision",
            context={
                "request_id": request_id,
                "probability": getattr(prediction_result, "probability", None),
                "risk_score": score.get("risk_score"),
                "decision": decision_str,
                "model_version": getattr(prediction_result, "model_version", None),
            },
        )
        session.commit()
        return [{"id": alert.id, "severity": alert.severity, "message": alert.message}]
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _persist_prediction(
    request_id: str,
    request: PredictionRequest,
    prediction_result: object,
    score: dict[str, object],
    decision: object,
    policy_evaluations: list[object],
    user: User,
) -> None:
    session = get_session()
    try:
        DecisionLogger(session).log(
            actor=user.username,
            action="predict",
            resource_type="model",
            resource_id=request_id,
            status=decision.decision if hasattr(decision, "decision") else str(decision),
            metadata={
                "request_id": request_id,
                "probability": getattr(prediction_result, "probability", None),
                "risk_score": score.get("risk_score"),
                "prediction": getattr(prediction_result, "prediction", None),
                "model_version": getattr(prediction_result, "model_version", None),
                "features": request.features,
                "engineered_features": getattr(prediction_result, "engineered_features", {}),
            },
        )
        decision_str = decision.decision if hasattr(decision, "decision") else str(decision)
        crud.create_prediction_record(
            session,
            {
                "request_id": request_id,
                "model_name": request.model_name,
                "model_version": getattr(prediction_result, "model_version", None),
                "raw_features": request.features,
                "engineered_features": getattr(prediction_result, "engineered_features", {}),
                "prediction": getattr(prediction_result, "prediction", None),
                "probability": getattr(prediction_result, "probability", None),
                "risk_score": score.get("risk_score"),
                "decision": decision_str,
                "explanations": {"prediction": getattr(prediction_result, "explanations", {}), "policy": [evaluation.__dict__ for evaluation in policy_evaluations]},
            },
        )
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@router.post("/predict", response_model=PredictionResponse)
def predict(
    request: PredictionRequest,
    background_tasks: BackgroundTasks,
    model_service = Depends(model_service_dep),
    policy_engine: PolicyEngine = Depends(policy_engine_dep),
    risk_scorer: RiskScorer = Depends(risk_scorer_dep),
    decision_engine: DecisionEngine = Depends(decision_engine_dep),
    user: User = Depends(get_current_active_user),
) -> PredictionResponse:
    request_id = request.request_id or str(uuid4())
    prediction_result = model_service.predict(model_name=request.model_name, model_version=request.model_version, features=request.features)
    policy_evaluations = policy_engine.evaluate(
        {
            "probability": prediction_result.probability,
            "risk_score": prediction_result.risk_score,
            "drift_score": 0.0,
            "amount": request.features.get("amount", 0.0),
        }
    )
    policy_penalty = 0.1 * sum(1 for evaluation in policy_evaluations if not evaluation.passed)
    score = risk_scorer.score(
        probability=prediction_result.probability,
        drift_score=0.0,
        data_quality_score=1.0,
        policy_penalty=policy_penalty,
        feature_risk_signals={key: abs(float(value)) for key, value in prediction_result.engineered_features.items() if isinstance(value, (int, float))},
    )
    decision = decision_engine.decide(
        probability=prediction_result.probability,
        risk_score=score["risk_score"],
        drift_score=0.0,
        policy_evaluations=policy_evaluations,
    )

    alerts = _create_alert(
        request_id,
        request,
        prediction_result,
        score,
        decision.decision if hasattr(decision, "decision") else str(decision),
    )

    response = PredictionResponse(
        request_id=request_id,
        model_name=request.model_name,
        model_version=prediction_result.model_version,
        prediction=prediction_result.prediction,
        probability=prediction_result.probability,
        risk_score=score["risk_score"],
        decision=decision.decision,
        explanations=prediction_result.explanations,
        alerts=alerts,
    )

    background_tasks.add_task(
        _persist_prediction,
        request_id=request_id,
        request=request,
        prediction_result=prediction_result,
        score=score,
        decision=decision,
        policy_evaluations=policy_evaluations,
        user=user,
    )

    return response
