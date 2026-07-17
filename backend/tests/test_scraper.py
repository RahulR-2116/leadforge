from __future__ import annotations

import logging
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.api.routes.scraper import get_job_manager
from app.db.base import Base
from app.main import app
from app.models import Business, Demo, FollowUp, Message, Statistic, User  # noqa: F401
from app.scraper.common.importer import BusinessImporter
from app.scraper.common.jobs import ScrapeJobManager
from app.scraper.common.models import ScrapedBusiness


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    """Create an isolated in-memory database session."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    session = testing_session_local()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_importer_skips_duplicate_phone(db_session: Session) -> None:
    """Importer skips scraped businesses that already exist by phone number."""
    logger = logging.getLogger("test")
    importer = BusinessImporter(db_session, logger)

    first = ScrapedBusiness(
        business_name="Apex Salon",
        category="Salon",
        phone_number="+91 90000 11111",
        address="12 High Street",
        city="Hyderabad",
        state=None,
        country="India",
        website=None,
        google_maps_url="https://www.google.com/maps/place/apex",
        rating=4.4,
        review_count=25,
        business_hours="Mon-Fri 10:00-20:00",
    )
    imported = importer.import_business(first)
    assert imported.imported is True

    duplicate = importer.import_business(
        ScrapedBusiness(
            business_name="Apex Salon Branch",
            category="Salon",
            phone_number="+91 90000 11111",
            address="14 High Street",
            city="Hyderabad",
            state=None,
            country="India",
            website=None,
            google_maps_url="https://www.google.com/maps/place/apex-branch",
            rating=None,
            review_count=None,
            business_hours=None,
        )
    )
    assert duplicate.duplicate is True
    assert duplicate.reason is not None
    assert "phone number" in duplicate.reason


def test_importer_ignores_social_media_websites(db_session: Session) -> None:
    """Importer marks social/listing URLs as missing official websites."""
    logger = logging.getLogger("test")
    importer = BusinessImporter(db_session, logger)

    result = importer.import_business(
        ScrapedBusiness(
            business_name="Social Salon",
            category="Salon",
            phone_number="+91 90000 22222",
            address="99 Lake Road",
            city="Hyderabad",
            state=None,
            country="India",
            website="https://instagram.com/socialsalon",
            google_maps_url="https://www.google.com/maps/place/social-salon",
            rating=4.2,
            review_count=19,
            business_hours=None,
        )
    )

    assert result.imported is True
    business = db_session.get(Business, result.business_id)
    assert business is not None
    assert business.website is None
    assert business.has_website is False


def test_google_maps_job_start_returns_progress(monkeypatch: pytest.MonkeyPatch) -> None:
    """Starting a scraper job returns queued progress without running a real browser."""
    manager = ScrapeJobManager()

    async def fake_runner(*_: object) -> None:
        return None

    app.dependency_overrides[get_job_manager] = lambda: manager
    monkeypatch.setattr("app.api.routes.scraper.run_google_maps_scrape", fake_runner)

    try:
        client = TestClient(app)
        response = client.post(
            "/api/v1/scraper/google-maps/start",
            json={"category": "Salon", "city": "Hyderabad", "maximum_results": 25},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 202
    payload = response.json()
    assert payload["source"] == "google_maps"
    assert payload["category"] == "Salon"
    assert payload["city"] == "Hyderabad"
    assert payload["maximum_results"] == 25

    latest = manager.latest_job()
    assert latest is not None
    assert latest.job_id == payload["job_id"]
