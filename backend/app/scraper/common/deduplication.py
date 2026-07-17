from __future__ import annotations

from difflib import SequenceMatcher

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.business import Business
from app.scraper.common.models import ScrapedBusiness


def find_duplicate_reason(
    db: Session, scraped: ScrapedBusiness, *, address_similarity_threshold: float
) -> str | None:
    """Return a duplicate reason for a scraped business, if one exists."""
    if scraped.phone_number:
        existing_by_phone = db.scalar(
            select(Business).where(Business.phone_number == scraped.phone_number).limit(1)
        )
        if existing_by_phone is not None:
            return f"phone number already exists on business #{existing_by_phone.id}"

    existing_by_name = db.scalar(
        select(Business)
        .where(func.lower(Business.business_name) == scraped.business_name.strip().lower())
        .limit(1)
    )
    if existing_by_name is not None:
        return f"business name already exists on business #{existing_by_name.id}"

    if not scraped.address:
        return None

    candidates = db.scalars(
        select(Business).where(
            or_(
                func.lower(Business.city) == (scraped.city or "").strip().lower(),
                func.lower(Business.business_name).like(f"%{scraped.business_name[:16].lower()}%"),
            )
        )
    ).all()

    normalized_address = _normalize_address(scraped.address)
    for candidate in candidates:
        if not candidate.address:
            continue
        score = SequenceMatcher(
            None, normalized_address, _normalize_address(candidate.address)
        ).ratio()
        if score >= address_similarity_threshold:
            return f"address is {score:.0%} similar to business #{candidate.id}"

    return None


def _normalize_address(address: str) -> str:
    """Normalize addresses for fuzzy similarity checks."""
    return " ".join(address.lower().replace(",", " ").split())
