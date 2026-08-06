from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field


class Settings(BaseModel):
    app_name: str = Field(default="Fraud Governance System")
    environment: str = Field(default="development")
    api_prefix: str = Field(default="/api/v1")
    database_url: str = Field(default="sqlite:///./fraud_governance.db")
    mlflow_tracking_uri: str = Field(default="file:./mlruns")
    model_store_path: str = Field(default="ml_model/artifacts")
    policies_path: str = Field(default="backend/governance/policies")
    log_level: str = Field(default="INFO")
    request_timeout_seconds: int = Field(default=30, ge=1)
    risk_threshold: float = Field(default=0.75, ge=0.0, le=1.0)
    review_threshold: float = Field(default=0.45, ge=0.0, le=1.0)
    drift_threshold: float = Field(default=0.2, ge=0.0, le=1.0)
    alert_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    retraining_threshold: float = Field(default=0.8, ge=0.0, le=1.0)
    allow_docs: bool = Field(default=True)

    def resolved_policies_path(self) -> Path:
        return Path(self.policies_path).resolve()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    data = {
        "app_name": os.getenv("APP_NAME", "Fraud Governance System"),
        "environment": os.getenv("ENVIRONMENT", "development"),
        "api_prefix": os.getenv("API_PREFIX", "/api/v1"),
        "database_url": os.getenv("DATABASE_URL", "sqlite:///./fraud_governance.db"),
        "mlflow_tracking_uri": os.getenv("MLFLOW_TRACKING_URI", "file:./mlruns"),
        "model_store_path": os.getenv("MODEL_STORE_PATH", "ml_model/artifacts"),
        "policies_path": os.getenv("POLICIES_PATH", "backend/governance/policies"),
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
        "request_timeout_seconds": int(os.getenv("REQUEST_TIMEOUT_SECONDS", "30")),
        "risk_threshold": float(os.getenv("RISK_THRESHOLD", "0.75")),
        "review_threshold": float(os.getenv("REVIEW_THRESHOLD", "0.45")),
        "drift_threshold": float(os.getenv("DRIFT_THRESHOLD", "0.2")),
        "alert_threshold": float(os.getenv("ALERT_THRESHOLD", "0.7")),
        "retraining_threshold": float(os.getenv("RETRAINING_THRESHOLD", "0.8")),
        "allow_docs": os.getenv("ALLOW_DOCS", "true").lower() in {"1", "true", "yes", "on"},
    }
    return Settings(**data)
