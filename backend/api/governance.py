from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.api.deps import (
    db_dep,
    decision_engine_dep,
    policy_engine_dep,
    risk_scorer_dep,
)
from backend.core.auth import get_current_active_user, require_roles
from backend.database import crud
from backend.database.models import AuditLog, User
from backend.governance.decision_engine import DecisionEngine
from backend.governance.drift_signal import drift_signal_from_psi
from backend.governance.policy_engine import PolicyEngine
from backend.governance.policy_loader import PolicyLoader
from backend.governance.risk_scoring import RiskScorer
from backend.schemas.governance import (
    DecisionRequest,
    DecisionResponse,
    PolicySchema,
    RiskScoreRequest,
    RiskScoreResponse,
)

router = APIRouter(tags=["governance"])


@router.get("/policies", response_model=list[PolicySchema])
def list_policies(session: Session = Depends(db_dep), user: User = Depends(get_current_active_user)) -> list[PolicySchema]:
    policies = crud.list_policies(session)
    if not policies:
        for loaded in PolicyLoader().load():
            crud.upsert_policy(session, loaded.config)
        policies = crud.list_policies(session)
    return [
        {
            "id": policy.id,
            "name": policy.name,
            "version": policy.version,
            "policy_type": policy.policy_type,
            "enabled": policy.enabled,
            "config": policy.config,
            "condition": policy.config.get("condition") or _extract_condition(policy.config),
            "action": policy.config.get("action") or _extract_action(policy.config),
            "escalation": policy.config.get("escalation") or _extract_escalation(policy.config),
            "lastModified": policy.updated_at.isoformat() if policy.updated_at else None,
            "modifiedBy": policy.config.get("modifiedBy", "system") if isinstance(policy.config, dict) else "system",
        }
        for policy in policies
    ]


def _extract_condition(config: dict[str, Any]) -> str | None:
    rules = config.get("rules")
    if isinstance(rules, list) and rules:
        first = rules[0]
        if isinstance(first, dict) and isinstance(first.get("if"), dict):
            return ", ".join(f"{k}: {v}" for k, v in first["if"].items())
    return None


def _extract_action(config: dict[str, Any]) -> str | None:
    rules = config.get("rules")
    if isinstance(rules, list) and rules:
        actions = []
        for rule in rules:
            if isinstance(rule, dict) and isinstance(rule.get("then"), dict):
                a = rule["then"].get("action")
                if a:
                    actions.append(a)
        if actions:
            return ", ".join(actions)
    return None


def _extract_escalation(config: dict[str, Any]) -> str | None:
    rules = config.get("rules")
    if isinstance(rules, list) and rules:
        reasons = []
        for rule in rules:
            if isinstance(rule, dict) and isinstance(rule.get("then"), dict):
                r = rule["then"].get("reason")
                if r:
                    reasons.append(r)
        if reasons:
            return "; ".join(reasons)
    return None


@router.get("/policies/history")
def policy_history(session: Session = Depends(db_dep), user: User = Depends(get_current_active_user), limit: int = 20) -> list[dict[str, Any]]:
    rows = session.scalars(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)).all()
    return [
        {
            "id": f"H-{index:03d}",
            "policyName": row.resource_id,
            "changedAt": row.created_at.isoformat(),
            "changedBy": row.actor,
            "changeSummary": row.payload.get("reason", f"{row.action} on {row.resource_type}") if isinstance(row.payload, dict) else f"{row.action} on {row.resource_type}",
        }
        for index, row in enumerate(rows)
    ]


@router.post("/policies/draft")
def save_draft(policy: dict[str, Any], session: Session = Depends(db_dep), user: User = Depends(get_current_active_user)) -> dict[str, Any]:
    payload = {
        "actor": policy.get("modifiedBy", user.username if user else "system"),
        "action": "policy_draft",
        "resource_type": "policy",
        "resource_id": policy.get("name", "unknown"),
        "status": "draft",
        "payload": {
            "reason": f"Published draft for {policy.get('name', 'unknown')}.",
            "policy": policy,
        },
    }
    crud.create_audit_log(session, payload)
    return {
        "id": f"H-{datetime.now(timezone.utc).timestamp():.0f}",
        "name": policy.get("name"),
        "lastModified": datetime.now(timezone.utc).isoformat(),
        "modifiedBy": policy.get("modifiedBy", user.username if user else "system"),
        "version": policy.get("version", "1.0"),
    }


@router.post("/policies")
def upsert_policy(payload: dict[str, object], session: Session = Depends(db_dep), user: User = Depends(require_roles("Compliance"))) -> dict[str, object]:
    policy = crud.upsert_policy(session, payload)
    return {
        "id": policy.name,
        "name": policy.name,
        "version": policy.version,
        "policy_type": policy.policy_type,
        "enabled": policy.enabled,
        "config": policy.config,
        "lastModified": policy.updated_at.isoformat() if policy.updated_at else None,
        "modifiedBy": payload.get("modifiedBy", "system"),
    }


@router.post("/policies/evaluate", response_model=list[dict[str, object]])
def evaluate_policies(request: dict[str, object], policy_engine: PolicyEngine = Depends(policy_engine_dep), user: User = Depends(get_current_active_user)) -> list[dict[str, object]]:
    return [evaluation.__dict__ for evaluation in policy_engine.evaluate(request)]


@router.post("/risk-score", response_model=RiskScoreResponse)
def compute_risk_score(request: RiskScoreRequest, scorer: RiskScorer = Depends(risk_scorer_dep), user: User = Depends(get_current_active_user)) -> RiskScoreResponse:
    result = scorer.score(
        probability=request.probability,
        drift_score=drift_signal_from_psi(request.raw_psi) if request.raw_psi is not None else request.drift_score,
        data_quality_score=request.data_quality_score,
        policy_penalty=request.policy_penalty,
        feature_risk_signals=request.feature_risk_signals,
    )
    return RiskScoreResponse(**result)


@router.post("/decision", response_model=DecisionResponse)
def compute_decision(request: DecisionRequest, engine: DecisionEngine = Depends(decision_engine_dep), user: User = Depends(get_current_active_user)) -> DecisionResponse:
    outcome = engine.decide(
        probability=request.probability,
        risk_score=request.risk_score,
        drift_score=request.drift_score,
        feature_risk_signals=request.feature_risk_signals,
    )
    return DecisionResponse(decision=outcome.decision, rationale=outcome.rationale, risk_score=outcome.risk_score, policy_status=outcome.policy_status)
