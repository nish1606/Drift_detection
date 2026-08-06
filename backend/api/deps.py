from __future__ import annotations

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from backend.core.config import Settings, get_settings
from backend.database.postgres import get_db
from backend.governance.decision_engine import DecisionEngine
from backend.governance.policy_engine import PolicyEngine
from backend.governance.policy_loader import PolicyLoader
from backend.governance.risk_scoring import RiskScorer
from backend.model.serve import FraudModelService
from backend.monitoring.metrics import MetricsCollector


def settings_dep() -> Settings:
    return get_settings()


def db_dep(session: Session = Depends(get_db)) -> Session:
    return session


def model_service_dep(session: Session = Depends(get_db)) -> FraudModelService:
    return FraudModelService(session=session, artifact_dir=get_settings().model_store_path)


def metrics_dep(request: Request) -> MetricsCollector:
    collector = getattr(request.app.state, "metrics_collector", None)
    if collector is None:
        collector = MetricsCollector()
        request.app.state.metrics_collector = collector
    return collector


def policy_engine_dep() -> PolicyEngine:
    policies = PolicyLoader().load()
    return PolicyEngine(policies)


def risk_scorer_dep() -> RiskScorer:
    return RiskScorer()


def decision_engine_dep() -> DecisionEngine:
    settings = get_settings()
    return DecisionEngine(review_threshold=settings.review_threshold, block_threshold=settings.risk_threshold, freeze_threshold=0.9)
