from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.api.deps import db_dep, decision_engine_dep, model_service_dep, policy_engine_dep, risk_scorer_dep
from backend.database import crud
from backend.governance.decision_engine import DecisionEngine
from backend.governance.policy_engine import PolicyEngine
from backend.governance.risk_scoring import RiskScorer
from backend.logging.decision_logger import DecisionLogger
from backend.response.alerting import AlertingService
from backend.schemas.prediction import PredictionRequest, PredictionResponse

router = APIRouter(tags=["prediction"])


@router.post("/predict", response_model=PredictionResponse)
def predict(
    request: PredictionRequest,
    session: Session = Depends(db_dep),
    model_service = Depends(model_service_dep),
    policy_engine: PolicyEngine = Depends(policy_engine_dep),
    risk_scorer: RiskScorer = Depends(risk_scorer_dep),
    decision_engine: DecisionEngine = Depends(decision_engine_dep),
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
    alerts: list[dict[str, object]] = []
    if decision.decision in {"block", "freeze", "review"}:
        alert = AlertingService(session).create_alert(
            severity="high" if decision.decision in {"block", "freeze"} else "medium",
            message=f"Prediction {decision.decision} for {request.model_name}",
            alert_type="prediction_decision",
            context={"request_id": request_id, "probability": prediction_result.probability, "risk_score": score["risk_score"]},
        )
        alerts.append({"id": alert.id, "severity": alert.severity, "message": alert.message})
    crud.create_prediction_record(
        session,
        {
            "request_id": request_id,
            "model_name": request.model_name,
            "model_version": prediction_result.model_version,
            "raw_features": request.features,
            "engineered_features": prediction_result.engineered_features,
            "prediction": prediction_result.prediction,
            "probability": prediction_result.probability,
            "risk_score": score["risk_score"],
            "decision": decision.decision,
            "explanations": {"prediction": prediction_result.explanations, "policy": [evaluation.__dict__ for evaluation in policy_evaluations]},
        },
    )
    DecisionLogger(session).log(
        actor="system",
        action="predict",
        resource_type="model",
        resource_id=request.model_name,
        status=decision.decision,
        metadata={"request_id": request_id, "risk_score": score["risk_score"]},
    )
    return PredictionResponse(
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
