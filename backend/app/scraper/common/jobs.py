from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock
from uuid import uuid4

from app.core.config import get_settings
from app.schemas.scraper import GoogleMapsScrapeRequest, ScrapeJobRead, ScrapeJobStatus


@dataclass
class ScrapeJob:
    """Mutable internal state for one scraper run."""

    job_id: str
    source: str
    category: str
    city: str
    maximum_results: int
    status: ScrapeJobStatus = ScrapeJobStatus.QUEUED
    current_task: str = "Queued"
    current_business: str | None = None
    businesses_found: int = 0
    businesses_processed: int = 0
    businesses_imported: int = 0
    duplicates_skipped: int = 0
    errors: list[str] = field(default_factory=list)
    log_file: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def progress(self) -> float:
        """Return progress as a percentage."""
        if self.maximum_results <= 0:
            return 0
        processed_progress = min(self.businesses_processed / self.maximum_results, 1)
        if self.status == ScrapeJobStatus.COMPLETED:
            return 100
        return round(processed_progress * 100, 2)

    @property
    def eta_seconds(self) -> int | None:
        """Estimate remaining seconds using current processing speed."""
        if not self.started_at or self.businesses_processed == 0:
            return None
        elapsed = (datetime.now(UTC) - self.started_at).total_seconds()
        per_business = elapsed / self.businesses_processed
        remaining = max(self.maximum_results - self.businesses_processed, 0)
        return int(per_business * remaining)

    def to_read(self) -> ScrapeJobRead:
        """Convert internal state to API response."""
        return ScrapeJobRead(
            job_id=self.job_id,
            source=self.source,
            status=self.status,
            category=self.category,
            city=self.city,
            maximum_results=self.maximum_results,
            current_task=self.current_task,
            current_business=self.current_business,
            progress=self.progress,
            businesses_found=self.businesses_found,
            businesses_processed=self.businesses_processed,
            businesses_imported=self.businesses_imported,
            duplicates_skipped=self.duplicates_skipped,
            errors=self.errors,
            eta_seconds=self.eta_seconds,
            log_file=self.log_file,
            started_at=self.started_at,
            completed_at=self.completed_at,
            created_at=self.created_at,
        )


class ScrapeJobManager:
    """Thread-safe in-memory job registry for scraper runs."""

    def __init__(self) -> None:
        self._jobs: dict[str, ScrapeJob] = {}
        self._lock = Lock()

    def create_google_maps_job(self, request: GoogleMapsScrapeRequest) -> ScrapeJob:
        """Create and register a queued Google Maps scrape job."""
        job = ScrapeJob(
            job_id=str(uuid4()),
            source="google_maps",
            category=request.category.strip(),
            city=request.city.strip(),
            maximum_results=request.maximum_results,
        )
        job.log_file = str(self._log_path(job))
        with self._lock:
            self._jobs[job.job_id] = job
        return job

    def get_job(self, job_id: str) -> ScrapeJob | None:
        """Return a scraper job by id."""
        with self._lock:
            return self._jobs.get(job_id)

    def latest_job(self) -> ScrapeJob | None:
        """Return the newest scraper job."""
        with self._lock:
            return max(self._jobs.values(), key=lambda job: job.created_at, default=None)

    def update(self, job_id: str, **changes: object) -> ScrapeJob:
        """Apply state changes to a job."""
        with self._lock:
            job = self._jobs[job_id]
            for key, value in changes.items():
                setattr(job, key, value)
            return job

    def append_error(self, job_id: str, message: str) -> None:
        """Append a bounded error message to a job."""
        with self._lock:
            job = self._jobs[job_id]
            job.errors.append(message)
            job.errors = job.errors[-20:]

    def create_logger(self, job: ScrapeJob) -> logging.Logger:
        """Create a per-job file logger."""
        log_path = self._log_path(job)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        logger = logging.getLogger(f"leadforge.scraper.{job.job_id}")
        logger.setLevel(get_settings().log_level.upper())
        logger.propagate = True
        logger.handlers.clear()
        handler = logging.FileHandler(log_path, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(handler)
        return logger

    @staticmethod
    def _log_path(job: ScrapeJob) -> Path:
        """Return the log path for a job."""
        safe_category = job.category.lower().replace(" ", "-")
        safe_city = job.city.lower().replace(" ", "-")
        filename = f"{job.created_at:%Y%m%d-%H%M%S}-{safe_category}-{safe_city}-{job.job_id}.log"
        return Path("logs") / "scrapes" / filename


job_manager = ScrapeJobManager()
