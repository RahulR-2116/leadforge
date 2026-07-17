from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from threading import Lock
from uuid import uuid4

from pydantic import BaseModel


class DemoJobRead(BaseModel):
    """Public demo generation job status."""

    job_id: str
    business_id: int
    status: str
    current_task: str
    progress: float
    demo_url: str | None
    errors: list[str]
    created_at: datetime
    completed_at: datetime | None


@dataclass
class DemoJob:
    """Mutable state for demo website generation."""

    job_id: str
    business_id: int
    status: str = "QUEUED"
    current_task: str = "Queued"
    progress: float = 0
    demo_url: str | None = None
    errors: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None

    def to_read(self) -> DemoJobRead:
        """Convert to API response."""
        return DemoJobRead(**self.__dict__)


class DemoJobManager:
    """Thread-safe in-memory demo job registry."""

    def __init__(self) -> None:
        self._jobs: dict[str, DemoJob] = {}
        self._lock = Lock()

    def create(self, business_id: int) -> DemoJob:
        """Create a queued demo job."""
        job = DemoJob(job_id=str(uuid4()), business_id=business_id)
        with self._lock:
            self._jobs[job.job_id] = job
        return job

    def get(self, job_id: str) -> DemoJob | None:
        """Return a demo job."""
        with self._lock:
            return self._jobs.get(job_id)

    def update(self, job_id: str, **changes: object) -> DemoJob:
        """Update demo job state."""
        with self._lock:
            job = self._jobs[job_id]
            for key, value in changes.items():
                setattr(job, key, value)
            return job


demo_job_manager = DemoJobManager()
