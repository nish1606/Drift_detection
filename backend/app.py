from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.api.drift import router as drift_router
from backend.api.governance import router as governance_router
from backend.api.health import router as health_router
from backend.api.monitoring import router as monitoring_router
from backend.api.predict import router as predict_router
from backend.api.transactions import router as transactions_router
from backend.core.config import Settings, get_settings
from backend.core.exceptions import FraudGovernanceError
from backend.core.middleware import RequestContextMiddleware, exception_response
from backend.database import crud
from backend.database.postgres import configure_engine, get_session, initialize_database
from backend.logging.logger import configure_logging
from backend.governance.policy_loader import PolicyLoader


def create_app(settings: Settings | None = None) -> FastAPI:
    active_settings = settings or get_settings()
    configure_logging(active_settings.log_level)
    configure_engine(active_settings.database_url)
    initialize_database()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        db = get_session()
        try:
            for loaded_policy in PolicyLoader(active_settings.policies_path).load():
                crud.upsert_policy(db, loaded_policy.config)
            yield
        finally:
            db.close()

    app = FastAPI(
        title=active_settings.app_name,
        docs_url="/docs" if active_settings.allow_docs else None,
        redoc_url=None,
        lifespan=lifespan,
    )
    app.state.settings = active_settings
    app.state.metrics_collector = None
    app.add_middleware(RequestContextMiddleware)

    @app.exception_handler(FraudGovernanceError)
    async def handle_exception(request, exc):
        return exception_response(exc)

    app.include_router(health_router, prefix=active_settings.api_prefix)
    app.include_router(predict_router, prefix=active_settings.api_prefix)
    app.include_router(governance_router, prefix=active_settings.api_prefix)
    app.include_router(monitoring_router, prefix=active_settings.api_prefix)
    app.include_router(drift_router, prefix=active_settings.api_prefix)
    app.include_router(transactions_router, prefix=active_settings.api_prefix)

    return app


app = create_app()
