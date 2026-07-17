from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import Business, Demo, FollowUp, Message, Statistic, User  # noqa: F401


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    """Create a test client backed by an isolated in-memory database."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db() -> Generator[Session, None, None]:
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)


def valid_business_payload(**overrides: object) -> dict[str, object]:
    """Return a valid business payload with optional overrides."""
    payload: dict[str, object] = {
        "business_name": "Acme Dental Studio",
        "category": "Dental Clinic",
        "phone_number": "+91 98765 43210",
        "email": "hello@acmedental.example",
        "address": "14 Market Road",
        "city": "Delhi",
        "state": "Delhi",
        "country": "India",
        "website": "https://acmedental.example",
        "google_maps_url": "https://maps.google.com/?q=acme",
        "rating": 4.6,
        "review_count": 83,
        "notes": "Good local lead",
    }
    payload.update(overrides)
    return payload


def create_business(client: TestClient, **overrides: object) -> dict[str, object]:
    """Create and return a business via the API."""
    response = client.post("/api/v1/businesses", json=valid_business_payload(**overrides))
    assert response.status_code == 201, response.text
    return response.json()


def test_business_crud_search_filter_sort_and_export(client: TestClient) -> None:
    """Business CRUD, search, filters, sorting, status updates, and exports work."""
    created = create_business(client)

    duplicate_phone = client.post(
        "/api/v1/businesses",
        json=valid_business_payload(business_name="Different Clinic"),
    )
    assert duplicate_phone.status_code == 409

    duplicate_name = client.post(
        "/api/v1/businesses",
        json=valid_business_payload(phone_number="+91 98765 43211"),
    )
    assert duplicate_name.status_code == 409

    invalid_phone = client.post(
        "/api/v1/businesses",
        json=valid_business_payload(business_name="Bad Phone", phone_number="abc"),
    )
    assert invalid_phone.status_code == 422

    create_business(
        client,
        business_name="Bright Fitness",
        category="Gym",
        phone_number="+91 98765 43212",
        city="Mumbai",
        state="Maharashtra",
        website=None,
        has_website=False,
        email=None,
        google_maps_url=None,
    )

    list_response = client.get("/api/v1/businesses", params={"search": "dental"})
    assert list_response.status_code == 200
    assert list_response.json()["total"] == 1

    filtered_response = client.get(
        "/api/v1/businesses",
        params={"city": "Mumbai", "has_website": "false", "sort_by": "business_name"},
    )
    assert filtered_response.status_code == 200
    assert filtered_response.json()["items"][0]["business_name"] == "Bright Fitness"

    detail_response = client.get(f"/api/v1/businesses/{created['id']}")
    assert detail_response.status_code == 200
    assert detail_response.json()["business_name"] == "Acme Dental Studio"

    update_response = client.patch(
        f"/api/v1/businesses/{created['id']}",
        json={"notes": "Booked discovery call", "status": "CONTACTED"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["notes"] == "Booked discovery call"

    status_response = client.patch(
        f"/api/v1/businesses/{created['id']}/status",
        json={"status": "DEMO_SENT"},
    )
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "DEMO_SENT"

    stats_response = client.get("/api/v1/businesses/stats")
    assert stats_response.status_code == 200
    assert stats_response.json()["demos_sent"] == 1

    csv_response = client.get("/api/v1/businesses/export", params={"format": "csv"})
    assert csv_response.status_code == 200
    assert "Acme Dental Studio" in csv_response.text

    xlsx_response = client.get("/api/v1/businesses/export", params={"format": "xlsx"})
    assert xlsx_response.status_code == 200
    assert xlsx_response.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    delete_response = client.delete(f"/api/v1/businesses/{created['id']}")
    assert delete_response.status_code == 204

    missing_response = client.get(f"/api/v1/businesses/{created['id']}")
    assert missing_response.status_code == 404


def test_business_history_records_are_created(client: TestClient) -> None:
    """Follow-ups, demos, and messages are attached to a business detail response."""
    created = create_business(client)

    follow_up_response = client.post(
        f"/api/v1/businesses/{created['id']}/follow-ups",
        json={"date": "2026-07-18T10:00:00+05:30", "completed": False, "notes": "Call owner"},
    )
    assert follow_up_response.status_code == 201

    demo_response = client.post(
        f"/api/v1/businesses/{created['id']}/demos",
        json={"demo_url": "https://demo.example/acme", "video_url": None, "notes": "Homepage demo"},
    )
    assert demo_response.status_code == 201

    message_response = client.post(
        f"/api/v1/businesses/{created['id']}/messages",
        json={
            "message": "Hi, I built a quick website audit.",
            "sent": True,
            "sent_at": "2026-07-17T12:00:00+05:30",
        },
    )
    assert message_response.status_code == 201

    detail_response = client.get(f"/api/v1/businesses/{created['id']}")
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert len(detail["follow_ups"]) == 1
    assert len(detail["demos"]) == 1
    assert len(detail["messages"]) == 1
