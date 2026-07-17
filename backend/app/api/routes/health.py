from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.db.session import get_db
from app.schemas.health import HealthCheck

router = APIRouter(tags=["health"])
logger = get_logger(__name__)


@router.get("/health", response_model=HealthCheck)
def health_check(
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> HealthCheck:
    """Return service health and verify database connectivity."""
    database_status = "ok"
    status = "ok"

    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        logger.exception("Database health check failed")
        database_status = "unavailable"
        status = "degraded"

    return HealthCheck(
        service=settings.app_name,
        status=status,
        environment=settings.app_env,
        database=database_status,
    )
