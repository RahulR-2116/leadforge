from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.business import Business


class Demo(Base):
    """A demo or consultation scheduled with a lead."""

    __tablename__ = "demos"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    business_id: Mapped[int] = mapped_column(
        ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False
    )
    demo_url: Mapped[str | None] = mapped_column(String(750), nullable=True)
    video_url: Mapped[str | None] = mapped_column(String(750), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    deployment_status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft")
    deployment_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revision_history: Mapped[str | None] = mapped_column(Text, nullable=True)
    template_used: Mapped[str | None] = mapped_column(String(120), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    business: Mapped[Business] = relationship(back_populates="demos")
