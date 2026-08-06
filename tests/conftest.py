from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app import create_app
from backend.core.config import Settings
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
    return create_app(settings)


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
