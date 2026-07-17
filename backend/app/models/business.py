from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.demo import Demo
    from app.models.follow_up import FollowUp
    from app.models.message import Message


class BusinessStatus(StrEnum):
    """Lead lifecycle states used by the CRM."""

    NEW = "NEW"
    CONTACTED = "CONTACTED"
    REPLIED = "REPLIED"
    DEMO_REQUESTED = "DEMO_REQUESTED"
    DEMO_SENT = "DEMO_SENT"
    NEGOTIATING = "NEGOTIATING"
    CLIENT = "CLIENT"
    LOST = "LOST"


class Business(Base):
    """A prospective business lead."""

    __tablename__ = "businesses"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    business_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    category: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    phone_number: Mapped[str | None] = mapped_column(
        String(32), nullable=True, unique=True, index=True
    )
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    city: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    state: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    country: Mapped[str | None] = mapped_column(String(120), nullable=True)
    website: Mapped[str | None] = mapped_column(String(500), nullable=True)
    has_website: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    google_maps_url: Mapped[str | None] = mapped_column(String(750), nullable=True)
    justdial_url: Mapped[str | None] = mapped_column(String(750), nullable=True)
    rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    review_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[BusinessStatus] = mapped_column(
        Enum(BusinessStatus, native_enum=False, length=32),
        nullable=False,
        default=BusinessStatus.NEW,
        index=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    follow_ups: Mapped[list[FollowUp]] = relationship(
        back_populates="business", cascade="all, delete-orphan"
    )
    demos: Mapped[list[Demo]] = relationship(
        back_populates="business", cascade="all, delete-orphan"
    )
    messages: Mapped[list[Message]] = relationship(
        back_populates="business", cascade="all, delete-orphan"
    )
