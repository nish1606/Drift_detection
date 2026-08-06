from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.api.deps import db_dep, decision_engine_dep, policy_engine_dep, risk_scorer_dep
from backend.database import crud
from backend.governance.decision_engine import DecisionEngine
from backend.governance.policy_engine import PolicyEngine
from backend.governance.policy_loader import PolicyLoader
from backend.governance.risk_scoring import RiskScorer
from backend.schemas.governance import DecisionRequest, DecisionResponse, PolicySchema, RiskScoreRequest, RiskScoreResponse

router = APIRouter(tags=["governance"])


@router.get("/policies", response_model=list[PolicySchema])
def list_policies(session: Session = Depends(db_dep)) -> list[PolicySchema]:
    policies = crud.list_policies(session)
    if not policies:
        for loaded in PolicyLoader().load():
            crud.upsert_policy(session, loaded.config)
        policies = crud.list_policies(session)
    return [PolicySchema(name=policy.name, version=policy.version, policy_type=policy.policy_type, enabled=policy.enabled, config=policy.config) for policy in policies]


@router.post("/policies/evaluate", response_model=list[dict[str, object]])
def evaluate_policies(request: dict[str, object], policy_engine: PolicyEngine = Depends(policy_engine_dep)) -> list[dict[str, object]]:
    return [evaluation.__dict__ for evaluation in policy_engine.evaluate(request)]


@router.post("/risk-score", response_model=RiskScoreResponse)
def compute_risk_score(request: RiskScoreRequest, scorer: RiskScorer = Depends(risk_scorer_dep)) -> RiskScoreResponse:
    result = scorer.score(
        probability=request.probability,
        drift_score=request.drift_score,
        data_quality_score=request.data_quality_score,
        policy_penalty=request.policy_penalty,
        feature_risk_signals=request.feature_risk_signals,
    )
    return RiskScoreResponse(**result)


@router.post("/decision", response_model=DecisionResponse)
def compute_decision(request: DecisionRequest, engine: DecisionEngine = Depends(decision_engine_dep)) -> DecisionResponse:
    outcome = engine.decide(
        probability=request.probability,
        risk_score=request.risk_score,
        drift_score=request.drift_score,
        feature_risk_signals=request.feature_risk_signals,
    )
    return DecisionResponse(decision=outcome.decision, rationale=outcome.rationale, risk_score=outcome.risk_score, policy_status=outcome.policy_status)
