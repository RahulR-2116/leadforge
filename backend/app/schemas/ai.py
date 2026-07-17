from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class AIGenerationType(StrEnum):
    """Supported sales assistant generation types."""

    WHATSAPP = "whatsapp"
    EMAIL = "email"
    FOLLOW_UP = "follow_up"
    AUDIT = "audit"
    PROPOSAL = "proposal"
    SUMMARY = "summary"


class AIGenerationRequest(BaseModel):
    """Generic business-bound generation request."""

    context: str | None = None


class FollowUpGenerationRequest(AIGenerationRequest):
    """Follow-up generation request."""

    scenario: str = Field(default="No reply", max_length=120)


class ObjectionRequest(BaseModel):
    """Customer objection input."""

    objection: str = Field(min_length=2, max_length=1000)


class ConversationRequest(BaseModel):
    """Conversation assistant input."""

    message: str = Field(min_length=1, max_length=2000)


class PromptUpdateRequest(BaseModel):
    """Prompt template update input."""

    template: str = Field(min_length=20)


class AIGenerationResponse(BaseModel):
    """AI generation response."""

    type: str
    content: str
    provider: str
    model: str


class EmailGenerationResponse(BaseModel):
    """Structured cold email response."""

    subject: str
    email: str
    cta: str
    provider: str
    model: str


class AuditResponse(BaseModel):
    """Website audit response."""

    score: int
    content: str
    provider: str
    model: str


class ProposalResponse(BaseModel):
    """Proposal response."""

    content: str
    provider: str
    model: str


class SalesInsightsResponse(BaseModel):
    """CRM sales insight response."""

    content: str
    generated_at: datetime


class DemoGenerateRequest(BaseModel):
    """Demo website generation request."""

    template: str


class DemoJobResponse(BaseModel):
    """Demo generation job response."""

    job_id: str
    business_id: int
    status: str
    current_task: str
    progress: float
    demo_url: str | None
    errors: list[str]
    created_at: datetime
    completed_at: datetime | None
