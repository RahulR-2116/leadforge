from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from app.schemas.scraper import GoogleMapsScrapeRequest, ScrapeJobRead
from app.scraper.common.jobs import ScrapeJobManager, job_manager
from app.scraper.google_maps.runner import run_google_maps_scrape

router = APIRouter(prefix="/scraper", tags=["scraper"])


def get_job_manager() -> ScrapeJobManager:
    """Return the process-local scraper job manager."""
    return job_manager


@router.post(
    "/google-maps/start", response_model=ScrapeJobRead, status_code=status.HTTP_202_ACCEPTED
)
async def start_google_maps_scrape(
    payload: GoogleMapsScrapeRequest,
    background_tasks: BackgroundTasks,
    manager: Annotated[ScrapeJobManager, Depends(get_job_manager)],
) -> ScrapeJobRead:
    """Start a Google Maps scrape in the background."""
    job = manager.create_google_maps_job(payload)
    background_tasks.add_task(run_google_maps_scrape, job, manager)
    return job.to_read()


@router.get("/jobs/latest", response_model=ScrapeJobRead | None)
def read_latest_scrape_job(
    manager: Annotated[ScrapeJobManager, Depends(get_job_manager)],
) -> ScrapeJobRead | None:
    """Return the latest scraper job for dashboard display."""
    job = manager.latest_job()
    return job.to_read() if job else None


@router.get("/jobs/{job_id}", response_model=ScrapeJobRead)
def read_scrape_job(
    job_id: str,
    manager: Annotated[ScrapeJobManager, Depends(get_job_manager)],
) -> ScrapeJobRead:
    """Return scraper job progress."""
    job = manager.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scraper job not found")
    return job.to_read()
