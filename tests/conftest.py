from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app import create_app
from backend.core.config import Settings
from backend.data.seed_users import seed_users
from backend.database.postgres import get_session


@pytest.fixture()
def settings(tmp_path: Path) -> Settings:
    return Settings(
        database_url=f"sqlite:///{tmp_path / 'fraud.db'}",
        model_store_path=str(tmp_path / "artifacts"),
        policies_path="backend/governance/policies",
        allow_docs=False,
    )


@pytest.fixture()
def app(settings: Settings):
    app = create_app(settings)
    db = get_session()
    try:
        seed_users(db)
    except Exception:
        pass
    finally:
        db.close()
    return app


@pytest.fixture()
def client(app):
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def db_session(app):
    session = get_session()
    try:
        yield session
    finally:
        session.close()
