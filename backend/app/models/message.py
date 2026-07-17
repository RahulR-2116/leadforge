from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Message(Base):
    """An outreach message sent or drafted for a lead."""

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    business_id: Mapped[int | None] = mapped_column(ForeignKey("businesses.id"), nullable=True)
    channel: Mapped[str] = mapped_column(String(50), nullable=False)
    subject: Mapped[str | None] = mapped_column(String(255), nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
