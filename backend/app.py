from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.auth import router as auth_router
from backend.api.drift import router as drift_router
from backend.api.explainability import router as explainability_router
from backend.api.governance import router as governance_router
from backend.api.health import router as health_router
from backend.api.monitoring import router as monitoring_router
from backend.api.predict import router as predict_router
from backend.api.predictions import router as predictions_router
from backend.api.transactions import router as transactions_router
from backend.core.config import Settings, get_settings
from backend.core.exceptions import FraudGovernanceError
from backend.core.middleware import RateLimitMiddleware, RequestContextMiddleware, exception_response
from backend.data.seed_users import seed_users
from backend.database import crud
from backend.database.postgres import configure_engine, get_session, initialize_database
from backend.governance.policy_loader import PolicyLoader
from backend.logging.logger import configure_logging
from backend.model.predict import FraudPredictor
from backend.streaming.live_stream import LiveTransactionStream

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BACKEND_DIR, "fraud_model.pkl")
SCALER_PATH = os.path.join(BACKEND_DIR, "scaler.pkl")
FEATURE_COLUMNS_PATH = os.path.join(BACKEND_DIR, "feature_columns.pkl")
MODEL_META_PATH = os.path.join(BACKEND_DIR, "model_meta.pkl")


def _load_predictor() -> FraudPredictor:
    """Load model artifacts once at startup — no per-request disk I/O."""
    predictor = FraudPredictor.from_artifacts(
        model_path=MODEL_PATH,
        scaler_path=SCALER_PATH,
        feature_columns_path=FEATURE_COLUMNS_PATH,
        model_meta_path=MODEL_META_PATH,
        baseline_stats_path=os.path.join(BACKEND_DIR, "baseline_stats.pkl"),
    )
    if predictor.model is None:
        print(f"[startup] No model found at {MODEL_PATH} — falling back to rule-based predictions")
    else:
        print(f"[startup] Fraud model v{predictor.model_version} loaded for real-time serving")
    return predictor


def create_app(settings: Settings | None = None) -> FastAPI:
    active_settings = settings or get_settings()
    configure_logging(active_settings.log_level)
    configure_engine(active_settings.database_url)
    initialize_database()
    db = get_session()
    try:
        seed_users(db)
    finally:
        db.close()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.fraud_predictor = _load_predictor()
        app.state.live_stream = LiveTransactionStream(interval_seconds=15, batch_size=3, predictor=app.state.fraud_predictor)
        db = get_session()
        try:
            for loaded_policy in PolicyLoader(active_settings.policies_path).load():
                try:
                    crud.upsert_policy(db, loaded_policy.config)
                except Exception as policy_error:
                    print(f"[startup] policy load error: {policy_error}")
            app.state.live_stream.start()
            yield
        finally:
            app.state.live_stream.stop()
            db.close()

    app = FastAPI(
        title=active_settings.app_name,
        docs_url="/docs" if active_settings.allow_docs else None,
        redoc_url=None,
        lifespan=lifespan,
    )
    app.state.settings = active_settings
    app.state.metrics_collector = None
    app.add_middleware(RateLimitMiddleware, limit=int(os.getenv("RATE_LIMIT_PER_MINUTE", "60")), window=60.0)
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:5174", "http://127.0.0.1:5174"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def ensure_cors_headers(request, call_next):
        response = await call_next(request)
        origin = request.headers.get("origin")
        if origin in {"http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:5174", "http://127.0.0.1:5174"}:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Request-ID, X-Role"
        return response

    @app.exception_handler(FraudGovernanceError)
    async def handle_exception(request, exc):
        return exception_response(exc)

    app.include_router(health_router, prefix=active_settings.api_prefix)
    app.include_router(auth_router, prefix=f"{active_settings.api_prefix}/auth")
    app.include_router(predict_router, prefix=active_settings.api_prefix)
    app.include_router(predictions_router, prefix=active_settings.api_prefix)
    app.include_router(governance_router, prefix=active_settings.api_prefix)
    app.include_router(monitoring_router, prefix=active_settings.api_prefix)
    app.include_router(drift_router, prefix=active_settings.api_prefix)
    app.include_router(explainability_router, prefix=active_settings.api_prefix)
    app.include_router(transactions_router, prefix=active_settings.api_prefix)

    return app


app = create_app()


