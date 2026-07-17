from __future__ import annotations

import logging

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.schemas.business import BusinessCreate
from app.scraper.common.deduplication import find_duplicate_reason
from app.scraper.common.models import ImportResult, ScrapedBusiness
from app.services.businesses import create_business
from app.services.website_detection import detect_official_website


class BusinessImporter:
    """Import scraped businesses directly into the CRM."""

    def __init__(self, db: Session, logger: logging.Logger) -> None:
        self._db = db
        self._logger = logger
        self._settings = get_settings()

    def import_business(self, scraped: ScrapedBusiness) -> ImportResult:
        """Deduplicate and save one scraped business."""
        duplicate_reason = find_duplicate_reason(
            self._db,
            scraped,
            address_similarity_threshold=self._settings.scraper_address_similarity_threshold,
        )
        if duplicate_reason is not None:
            self._logger.info("Skipping duplicate %s: %s", scraped.business_name, duplicate_reason)
            return ImportResult(
                imported=False,
                duplicate=True,
                reason=duplicate_reason,
                business_id=None,
            )

        notes_parts = ["Imported from Google Maps."]
        if scraped.business_hours:
            notes_parts.append(f"Business hours: {scraped.business_hours}")

        try:
            official_website = detect_official_website(scraped.website)
            created = create_business(
                self._db,
                BusinessCreate(
                    business_name=scraped.business_name,
                    category=scraped.category,
                    phone_number=scraped.phone_number,
                    address=scraped.address,
                    city=scraped.city,
                    state=scraped.state,
                    country=scraped.country,
                    website=official_website,
                    has_website=official_website is not None,
                    google_maps_url=scraped.google_maps_url,
                    rating=scraped.rating,
                    review_count=scraped.review_count,
                    notes="\n".join(notes_parts),
                ),
            )
        except HTTPException as exc:
            reason = str(exc.detail)
            self._logger.info("Skipping duplicate %s: %s", scraped.business_name, reason)
            return ImportResult(imported=False, duplicate=True, reason=reason, business_id=None)

        self._logger.info("Imported %s as business #%s", scraped.business_name, created.id)
        return ImportResult(imported=True, duplicate=False, reason=None, business_id=created.id)
