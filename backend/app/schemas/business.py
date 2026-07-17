from __future__ import annotations

import re
from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    HttpUrl,
    field_validator,
    model_validator,
)

from app.models.business import BusinessStatus
from app.services.website_detection import has_official_website

PHONE_PATTERN = re.compile(r"^\+?[0-9][0-9\s().-]{6,24}$")


def normalize_url(value: HttpUrl | str | None) -> str | None:
    """Convert optional URL values to strings for storage."""
    return str(value) if value is not None else None


class FollowUpBase(BaseModel):
    """Shared follow-up fields."""

    date: datetime
    completed: bool = False
    notes: str | None = None


class FollowUpCreate(FollowUpBase):
    """Payload for creating a follow-up."""


class FollowUpRead(FollowUpBase):
    """Follow-up response payload."""

    id: int
    business_id: int

    model_config = ConfigDict(from_attributes=True)


class DemoBase(BaseModel):
    """Shared demo fields."""

    demo_url: HttpUrl | None = None
    video_url: HttpUrl | None = None
    notes: str | None = None


class DemoCreate(DemoBase):
    """Payload for creating demo history."""


class DemoRead(BaseModel):
    """Demo response payload."""

    id: int
    business_id: int
    demo_url: str | None
    video_url: str | None
    notes: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MessageBase(BaseModel):
    """Shared message fields."""

    message: str = Field(min_length=1)
    sent: bool = False
    sent_at: datetime | None = None


class MessageCreate(MessageBase):
    """Payload for creating message history."""


class MessageRead(MessageBase):
    """Message response payload."""

    id: int
    business_id: int

    model_config = ConfigDict(from_attributes=True)


class BusinessBase(BaseModel):
    """Shared business lead fields."""

    business_name: str = Field(min_length=2, max_length=255)
    category: str | None = Field(default=None, max_length=120)
    phone_number: str | None = Field(default=None, max_length=32)
    email: EmailStr | None = None
    address: str | None = Field(default=None, max_length=500)
    city: str | None = Field(default=None, max_length=120)
    state: str | None = Field(default=None, max_length=120)
    country: str | None = Field(default=None, max_length=120)
    website: HttpUrl | None = None
    has_website: bool = False
    google_maps_url: HttpUrl | None = None
    justdial_url: HttpUrl | None = None
    rating: float | None = Field(default=None, ge=0, le=5)
    review_count: int | None = Field(default=None, ge=0)
    status: BusinessStatus = BusinessStatus.NEW
    notes: str | None = None

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value: str | None) -> str | None:
        """Validate and trim phone numbers while allowing common punctuation."""
        if value is None:
            return value
        normalized = value.strip()
        if not PHONE_PATTERN.match(normalized):
            raise ValueError(
                "Phone number must contain 7-25 digits and may include +, spaces, (), ., or -"
            )
        return normalized

    @model_validator(mode="before")
    @classmethod
    def infer_has_website(cls, values: object) -> object:
        """Mark leads with an official website when one is supplied."""
        if isinstance(values, dict) and values.get("website") and "has_website" not in values:
            values["has_website"] = has_official_website(str(values["website"]))
        return values


class BusinessCreate(BusinessBase):
    """Payload for creating a business lead."""


class BusinessUpdate(BaseModel):
    """Payload for updating a business lead."""

    business_name: str | None = Field(default=None, min_length=2, max_length=255)
    category: str | None = Field(default=None, max_length=120)
    phone_number: str | None = Field(default=None, max_length=32)
    email: EmailStr | None = None
    address: str | None = Field(default=None, max_length=500)
    city: str | None = Field(default=None, max_length=120)
    state: str | None = Field(default=None, max_length=120)
    country: str | None = Field(default=None, max_length=120)
    website: HttpUrl | None = None
    has_website: bool | None = None
    google_maps_url: HttpUrl | None = None
    justdial_url: HttpUrl | None = None
    rating: float | None = Field(default=None, ge=0, le=5)
    review_count: int | None = Field(default=None, ge=0)
    status: BusinessStatus | None = None
    notes: str | None = None

    _validate_phone_number = field_validator("phone_number")(BusinessBase.validate_phone_number)


class BusinessStatusUpdate(BaseModel):
    """Payload for updating only lead status."""

    status: BusinessStatus


class BusinessRead(BaseModel):
    """Business lead response payload."""

    id: int
    business_name: str
    category: str | None
    phone_number: str | None
    email: str | None
    address: str | None
    city: str | None
    state: str | None
    country: str | None
    website: str | None
    has_website: bool
    google_maps_url: str | None
    justdial_url: str | None
    rating: float | None
    review_count: int | None
    status: BusinessStatus
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BusinessDetail(BusinessRead):
    """Business lead response with related CRM history."""

    follow_ups: list[FollowUpRead] = Field(default_factory=list)
    demos: list[DemoRead] = Field(default_factory=list)
    messages: list[MessageRead] = Field(default_factory=list)


class BusinessList(BaseModel):
    """Paginated business lead response."""

    items: list[BusinessRead]
    total: int
    page: int
    page_size: int
    pages: int


class BusinessStats(BaseModel):
    """Dashboard CRM metrics."""

    total_businesses: int
    contacted: int
    replies: int
    demos_sent: int
    clients_won: int
    lost: int
    businesses_with_websites: int
    businesses_without_websites: int
