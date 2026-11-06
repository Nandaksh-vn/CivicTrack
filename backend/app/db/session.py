"""
CivicTrack - SQLAlchemy engine and session factory (TRD sections 5.3 and 6.2).
"""
from __future__ import annotations

from collections.abc import Generator
from typing import Any

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

_is_sqlite = settings.database_url.startswith("sqlite")
_connect_args: dict[str, Any] = (
    {"check_same_thread": False} if _is_sqlite else {"connect_timeout": 5, "charset": "utf8mb4"}
)

engine = create_engine(
    settings.database_url,
    pool_size=10,
    max_overflow=20,
    pool_recycle=1800,
    pool_pre_ping=True,
    connect_args=_connect_args,
    echo=False,
)


if engine.dialect.name == "mysql":

    @event.listens_for(engine, "connect")
    def _set_session_options(dbapi_conn: Any, _connection_record: Any) -> None:
        """Force READ COMMITTED, UTC storage, and utf8mb4 on every connection."""
        with dbapi_conn.cursor() as cursor:
            cursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")
            cursor.execute("SET time_zone = '+00:00'")
            cursor.execute("SET NAMES utf8mb4")


SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
