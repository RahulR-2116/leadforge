from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class ScrapeJobStatus(StrEnum):
    """Lifecycle status for a scraper background job."""

    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class GoogleMapsScrapeRequest(BaseModel):
    """Input for starting a Google Maps scrape."""

    category: str = Field(min_length=2, max_length=120)
    city: str = Field(min_length=2, max_length=120)
    maximum_results: int = Field(default=50, ge=1, le=500)


class ScrapeJobRead(BaseModel):
    """Public scraper job status."""

    job_id: str
    source: str
    status: ScrapeJobStatus
    category: str
    city: str
    maximum_results: int
    current_task: str
    current_business: str | None
    progress: float
    businesses_found: int
    businesses_processed: int
    businesses_imported: int
    duplicates_skipped: int
    errors: list[str]
    eta_seconds: int | None
    log_file: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
