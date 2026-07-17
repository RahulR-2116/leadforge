from __future__ import annotations

import json
from collections.abc import Generator

import pytest
from sqlalchemy import StaticPool, create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.ai.models.core import AIRequest, AIResponse
from app.ai.providers.base import AIProvider
from app.ai.services.demo_generator import DemoWebsiteGenerator
from app.ai.services.sales_assistant import SalesAssistantService
from app.db.base import Base
from app.models import Business, Demo, FollowUp, Message, Statistic, User  # noqa: F401
from app.models.business import BusinessStatus


class FakeProvider(AIProvider):
    """Deterministic provider for tests."""

    async def generate(self, request: AIRequest) -> AIResponse:
        """Return deterministic content based on the prompt."""
        joined = "\n".join(message.content for message in request.messages)
        if "subject, email, and cta" in joined:
            content = json.dumps(
                {
                    "subject": "A better website for your clinic",
                    "email": "Hi, here is a concise outreach email.",
                    "cta": "Can we speak this week?",
                }
            )
        elif "score and content" in joined:
            content = json.dumps({"score": 72, "content": "Audit content"})
        elif "heroHeadline" in joined:
            content = json.dumps(
                {
                    "heroHeadline": "Modern care for local customers",
                    "about": "Client-review demo copy.",
                    "services": ["Consultation", "Booking"],
                    "faq": ["Sample FAQ for client review."],
                    "seoTitle": "Demo Website",
                    "seoDescription": "Demo description",
                    "metaKeywords": "demo, website",
                    "cta": "Book now",
                    "testimonials": ["Sample testimonial for client review."],
                }
            )
        else:
            content = "Generated sales content"
        return AIResponse(content=content, provider="fake", model=request.model)


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
    session.add(
        Business(
            business_name="Bright Dental",
            category="Dental Clinic",
            phone_number="+91 90000 33333",
            city="Hyderabad",
            address="12 Smile Road",
            has_website=False,
            status=BusinessStatus.NEW,
        )
    )
    session.commit()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.mark.anyio
async def test_sales_assistant_generates_structured_email(db_session: Session) -> None:
    """Sales assistant parses structured email output."""
    business = db_session.scalar(select(Business))
    assert business is not None

    service = SalesAssistantService(db_session, provider=FakeProvider())
    response = await service.generate_email(business.id)

    assert response.subject == "A better website for your clinic"
    assert response.cta == "Can we speak this week?"


@pytest.mark.anyio
async def test_demo_generator_creates_demo_record(db_session: Session) -> None:
    """Demo generator renders and stores a demo record."""
    business = db_session.scalar(select(Business))
    assert business is not None

    generator = DemoWebsiteGenerator(db_session, provider=FakeProvider())
    demo = await generator.generate(business_id=business.id, template="dental_clinic")

    assert demo.demo_url is not None
    assert demo.template_used == "dental_clinic"
    assert demo.version == 1
    assert demo.deployment_status in {"generated", "deployed"}
