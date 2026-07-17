from __future__ import annotations

import json
from datetime import UTC, datetime
from io import BytesIO

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ai.models.core import AIRequest, AIResponse, ChatMessage
from app.ai.prompts.library import PromptLibrary, prompt_library
from app.ai.providers.base import AIProvider
from app.ai.providers.factory import get_ai_provider
from app.core.config import Settings, get_settings
from app.models.business import Business, BusinessStatus
from app.models.message import Message
from app.schemas.ai import (
    AIGenerationResponse,
    AuditResponse,
    EmailGenerationResponse,
    ProposalResponse,
    SalesInsightsResponse,
)
from app.services.businesses import get_business_or_404


class SalesAssistantService:
    """AI-powered sales assistant for CRM leads."""

    def __init__(
        self,
        db: Session,
        provider: AIProvider | None = None,
        settings: Settings | None = None,
        prompts: PromptLibrary | None = None,
    ) -> None:
        self._db = db
        self._settings = settings or get_settings()
        self._provider = provider or get_ai_provider(self._settings)
        self._prompts = prompts or prompt_library

    async def generate_whatsapp(
        self, business_id: int, *, context: str | None = None
    ) -> AIGenerationResponse:
        """Generate a personalized WhatsApp outreach message."""
        business = get_business_or_404(self._db, business_id)
        content = await self._generate(
            "whatsapp",
            business,
            extra=(
                "Maximum 120 words. Short, conversational, professional, never spammy. "
                f"Extra context: {context or 'none'}"
            ),
        )
        self._save_message(business.id, content.content)
        return AIGenerationResponse(type="whatsapp", **content.__dict__)

    async def generate_email(self, business_id: int) -> EmailGenerationResponse:
        """Generate a cold email with subject, body, and CTA."""
        business = get_business_or_404(self._db, business_id)
        response = await self._generate(
            "email",
            business,
            extra="Return JSON with subject, email, and cta keys. Do not use markdown fences.",
        )
        parsed = _json_or_fallback(response.content)
        return EmailGenerationResponse(
            subject=str(parsed.get("subject", f"Website ideas for {business.business_name}")),
            email=str(parsed.get("email", response.content)),
            cta=str(parsed.get("cta", "Would you be open to a quick 10-minute call?")),
            provider=response.provider,
            model=response.model,
        )

    async def generate_follow_up(
        self, business_id: int, *, scenario: str, context: str | None = None
    ) -> AIGenerationResponse:
        """Generate a status-aware follow-up."""
        business = get_business_or_404(self._db, business_id)
        response = await self._generate(
            "follow_up",
            business,
            extra=(
                f"CRM status: {business.status.value}. Scenario: {scenario}. "
                f"Context: {context or 'none'}"
            ),
        )
        return AIGenerationResponse(type="follow_up", **response.__dict__)

    async def generate_audit(self, business_id: int) -> AuditResponse:
        """Generate a website audit or no-website opportunity report."""
        business = get_business_or_404(self._db, business_id)
        instruction = (
            "If website exists, analyze navigation, homepage, speed, SEO, mobile responsiveness, "
            "SSL, accessibility, CTAs, contact section, maps, WhatsApp, and booking. "
            "If no website exists, explain benefits a website could provide. "
            "Return JSON with score and content. Do not fabricate factual claims."
        )
        response = await self._generate("audit", business, extra=instruction)
        parsed = _json_or_fallback(response.content)
        score = int(parsed.get("score", 0 if not business.has_website else 60))
        return AuditResponse(
            score=max(0, min(score, 100)),
            content=str(parsed.get("content", response.content)),
            provider=response.provider,
            model=response.model,
        )

    async def generate_proposal(self, business_id: int) -> ProposalResponse:
        """Generate a professional proposal."""
        business = get_business_or_404(self._db, business_id)
        response = await self._generate(
            "proposal",
            business,
            extra=(
                "Include overview, problems, recommended solution, deliverables, timeline, "
                "price placeholder, maintenance, and support."
            ),
        )
        return ProposalResponse(
            content=response.content, provider=response.provider, model=response.model
        )

    async def generate_summary(self, business_id: int) -> AIGenerationResponse:
        """Generate lead summary, objections, services, pricing strategy, and upsells."""
        business = get_business_or_404(self._db, business_id)
        response = await self._generate("summary", business, extra="Be concise and practical.")
        return AIGenerationResponse(type="summary", **response.__dict__)

    async def generate_objection_replies(self, objection: str) -> AIGenerationResponse:
        """Generate three professional objection-handling replies."""
        response = await self._provider.generate(
            self._request(
                [
                    ChatMessage(role="system", content=self._prompts.list_prompts()["objection"]),
                    ChatMessage(
                        role="user",
                        content=(
                            f"Customer objection: {objection}\n"
                            "Return exactly three reply options."
                        ),
                    ),
                ]
            )
        )
        return AIGenerationResponse(type="objection", **response.__dict__)

    async def generate_conversation_reply(
        self, business_id: int, message: str
    ) -> AIGenerationResponse:
        """Generate contextual reply using previous CRM messages as memory."""
        business = get_business_or_404(self._db, business_id)
        previous = self._db.scalars(
            select(Message)
            .where(Message.business_id == business_id)
            .order_by(Message.id.desc())
            .limit(8)
        ).all()
        memory = "\n".join(reversed([item.message for item in previous]))
        response = await self._provider.generate(
            self._request(
                [
                    ChatMessage(
                        role="system",
                        content=self._prompts.list_prompts()["conversation"],
                    ),
                    ChatMessage(
                        role="user",
                        content=(
                            f"Business: {business.business_name}\n"
                            f"Previous conversation:\n{memory}\n"
                            f"Latest customer message: {message}\nGenerate the next reply."
                        ),
                    ),
                ]
            )
        )
        self._save_message(business_id, message, sent=False)
        return AIGenerationResponse(type="conversation", **response.__dict__)

    def generate_sales_insights(self) -> SalesInsightsResponse:
        """Analyze CRM data using deterministic statistics."""
        total = self._db.scalar(select(func.count(Business.id))) or 0
        clients = (
            self._db.scalar(
                select(func.count(Business.id)).where(Business.status == BusinessStatus.CLIENT)
            )
            or 0
        )
        lost = (
            self._db.scalar(
                select(func.count(Business.id)).where(Business.status == BusinessStatus.LOST)
            )
            or 0
        )
        best_category = self._best_group(Business.category)
        best_city = self._best_group(Business.city)
        conversion_rate = round((clients / total) * 100, 2) if total else 0
        content = (
            f"Total leads: {total}\n"
            f"Conversion rate: {conversion_rate}%\n"
            f"Clients won: {clients}\n"
            f"Lost leads: {lost}\n"
            f"Best converting category signal: {best_category}\n"
            f"Best converting city signal: {best_city}\n"
            "Average close time, lost reasons, and best performing message require richer activity "
            "timestamps and outcome tagging in future workflow data."
        )
        return SalesInsightsResponse(content=content, generated_at=datetime.now(UTC))

    def proposal_pdf(self, proposal: str) -> bytes:
        """Render proposal text as a PDF."""
        output = BytesIO()
        pdf = canvas.Canvas(output, pagesize=letter)
        width, height = letter
        y = height - 72
        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawString(72, y, "LeadForge Proposal")
        y -= 32
        pdf.setFont("Helvetica", 10)
        for line in proposal.splitlines():
            for chunk in _wrap(line, 95):
                if y < 72:
                    pdf.showPage()
                    pdf.setFont("Helvetica", 10)
                    y = height - 72
                pdf.drawString(72, y, chunk)
                y -= 14
        pdf.save()
        return output.getvalue()

    async def _generate(self, prompt_key: str, business: Business, *, extra: str) -> AIResponse:
        prompts = self._prompts.list_prompts()
        business_context = (
            f"Business: {business.business_name}\n"
            f"Category: {business.category}\nCity: {business.city}\n"
            "Website status: "
            f"{'has official website' if business.has_website else 'no official website'}\n"
            f"Website: {business.website or 'none'}\nRating: {business.rating}\n"
            f"Review count: {business.review_count}\nNotes: {business.notes or 'none'}"
        )
        return await self._provider.generate(
            self._request(
                [
                    ChatMessage(role="system", content=prompts[prompt_key]),
                    ChatMessage(
                        role="user",
                        content=f"{business_context}\n\nInstructions: {extra}",
                    ),
                ]
            )
        )

    def _request(self, messages: list[ChatMessage]) -> AIRequest:
        return AIRequest(
            messages=messages,
            model=self._settings.ai_model,
            temperature=self._settings.ai_temperature,
            max_tokens=self._settings.ai_max_tokens,
        )

    def _save_message(self, business_id: int, message: str, *, sent: bool = True) -> None:
        self._db.add(Message(business_id=business_id, message=message, sent=sent))
        self._db.commit()

    def _best_group(self, column: object) -> str:
        row = self._db.execute(
            select(column, func.count(Business.id))
            .where(Business.status == BusinessStatus.CLIENT)
            .group_by(column)
            .order_by(func.count(Business.id).desc())
            .limit(1)
        ).first()
        return str(row[0]) if row and row[0] else "Not enough converted leads yet"


def _json_or_fallback(content: str) -> dict[str, object]:
    try:
        parsed = json.loads(content)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}


def _wrap(line: str, width: int) -> list[str]:
    if not line:
        return [""]
    return [line[index : index + width] for index in range(0, len(line), width)]
