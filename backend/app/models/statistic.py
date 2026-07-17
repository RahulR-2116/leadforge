from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Statistic(Base):
    """A named metric captured for CRM and lead generation reporting."""

    __tablename__ = "statistics"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    metric_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    metric_value: Mapped[float] = mapped_column(Float, nullable=False)
    period: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
