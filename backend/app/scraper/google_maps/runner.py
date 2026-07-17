from __future__ import annotations

from datetime import UTC, datetime

from app.db.session import SessionLocal
from app.schemas.scraper import ScrapeJobStatus
from app.scraper.common.importer import BusinessImporter
from app.scraper.common.jobs import ScrapeJob, ScrapeJobManager
from app.scraper.google_maps.scraper import GoogleMapsScraper


async def run_google_maps_scrape(job: ScrapeJob, manager: ScrapeJobManager) -> None:
    """Run a Google Maps scrape job and import results into the CRM."""
    logger = manager.create_logger(job)
    manager.update(
        job.job_id,
        status=ScrapeJobStatus.RUNNING,
        started_at=datetime.now(UTC),
        current_task="Opening Google Maps",
    )
    logger.info(
        "Starting Google Maps scrape: category=%s city=%s maximum_results=%s",
        job.category,
        job.city,
        job.maximum_results,
    )

    db = SessionLocal()
    importer = BusinessImporter(db, logger)
    scraper = GoogleMapsScraper(logger)

    try:
        async for scraped in scraper.scrape(
            category=job.category,
            city=job.city,
            maximum_results=job.maximum_results,
        ):
            manager.update(
                job.job_id,
                current_task="Importing business",
                current_business=scraped.business_name,
                businesses_found=job.businesses_found + 1,
            )
            result = importer.import_business(scraped)
            manager.update(
                job.job_id,
                businesses_processed=job.businesses_processed + 1,
                businesses_imported=job.businesses_imported + (1 if result.imported else 0),
                duplicates_skipped=job.duplicates_skipped + (1 if result.duplicate else 0),
            )

        manager.update(
            job.job_id,
            status=ScrapeJobStatus.COMPLETED,
            current_task="Completed",
            current_business=None,
            completed_at=datetime.now(UTC),
        )
        logger.info(
            "Completed scrape: found=%s imported=%s duplicates=%s errors=%s",
            job.businesses_found,
            job.businesses_imported,
            job.duplicates_skipped,
            len(job.errors),
        )
    except Exception as exc:
        logger.exception("Google Maps scrape failed")
        manager.append_error(job.job_id, str(exc))
        manager.update(
            job.job_id,
            status=ScrapeJobStatus.FAILED,
            current_task="Failed",
            completed_at=datetime.now(UTC),
        )
    finally:
        db.close()
