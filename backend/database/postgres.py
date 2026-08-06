from __future__ import annotations

from collections.abc import Generator
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.core.config import get_settings


class Base(DeclarativeBase):
    pass


_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def _create_engine(database_url: str) -> Engine:
    kwargs: dict[str, Any] = {"future": True, "pool_pre_ping": True}
    if database_url.startswith("sqlite"):
        kwargs.update({"connect_args": {"check_same_thread": False}, "poolclass": StaticPool})
    return create_engine(database_url, **kwargs)


def configure_engine(database_url: str | None = None) -> Engine:
    global _engine, _SessionLocal
    resolved_url = database_url or get_settings().database_url
    _engine = _create_engine(resolved_url)
    _SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False, expire_on_commit=False, future=True)
    return _engine


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        return configure_engine()
    return _engine


def get_session() -> Session:
    global _SessionLocal
    if _SessionLocal is None:
        configure_engine()
    assert _SessionLocal is not None
    return _SessionLocal()


def get_db() -> Generator[Session, None, None]:
    session = get_session()
    try:
        yield session
    finally:
        session.close()


def initialize_database() -> None:
    from backend.database.models import Base as ModelsBase

    ModelsBase.metadata.create_all(bind=get_engine())
