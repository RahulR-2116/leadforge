from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScrapedBusiness:
    """Business data extracted from an external lead source."""

    business_name: str
    category: str | None
    phone_number: str | None
    address: str | None
    city: str | None
    state: str | None
    country: str | None
    website: str | None
    google_maps_url: str | None
    rating: float | None
    review_count: int | None
    business_hours: str | None


@dataclass(frozen=True)
class ImportResult:
    """Result of attempting to import one scraped business."""

    imported: bool
    duplicate: bool
    reason: str | None
    business_id: int | None
