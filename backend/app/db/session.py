from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


def create_database_engine(database_url: str | None = None) -> Engine:
    """Create a SQLAlchemy engine for SQLite development or PostgreSQL production."""
    resolved_url = database_url or get_settings().database_url
    connect_args = {"check_same_thread": False} if resolved_url.startswith("sqlite") else {}
    return create_engine(resolved_url, connect_args=connect_args, pool_pre_ping=True)


engine = create_database_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Yield a database session for FastAPI dependencies."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
