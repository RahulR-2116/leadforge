from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.ai.prompts.library import prompt_library
from app.ai.services.demo_generator import run_demo_generation_job
from app.ai.services.demo_jobs import DemoJobManager, demo_job_manager
from app.ai.services.sales_assistant import SalesAssistantService
from app.ai.services.templates import TemplateEngine
from app.db.session import get_db
from app.schemas.ai import (
    AIGenerationRequest,
    AIGenerationResponse,
    AuditResponse,
    ConversationRequest,
    DemoGenerateRequest,
    DemoJobResponse,
    EmailGenerationResponse,
    FollowUpGenerationRequest,
    ObjectionRequest,
    PromptUpdateRequest,
    ProposalResponse,
    SalesInsightsResponse,
)

router = APIRouter(prefix="/ai", tags=["ai"])


def get_demo_job_manager() -> DemoJobManager:
    """Return the process-local demo job manager."""
    return demo_job_manager


@router.post("/businesses/{business_id}/whatsapp", response_model=AIGenerationResponse)
async def generate_whatsapp(
    business_id: int,
    payload: AIGenerationRequest,
    db: Annotated[Session, Depends(get_db)],
) -> AIGenerationResponse:
    """Generate personalized WhatsApp outreach."""
    return await SalesAssistantService(db).generate_whatsapp(business_id, context=payload.context)


@router.post("/businesses/{business_id}/email", response_model=EmailGenerationResponse)
async def generate_email(
    business_id: int,
    db: Annotated[Session, Depends(get_db)],
) -> EmailGenerationResponse:
    """Generate a cold email."""
    return await SalesAssistantService(db).generate_email(business_id)


@router.post("/businesses/{business_id}/follow-up", response_model=AIGenerationResponse)
async def generate_follow_up(
    business_id: int,
    payload: FollowUpGenerationRequest,
    db: Annotated[Session, Depends(get_db)],
) -> AIGenerationResponse:
    """Generate a CRM-status-aware follow-up."""
    return await SalesAssistantService(db).generate_follow_up(
        business_id, scenario=payload.scenario, context=payload.context
    )


@router.post("/businesses/{business_id}/audit", response_model=AuditResponse)
async def generate_audit(
    business_id: int,
    db: Annotated[Session, Depends(get_db)],
) -> AuditResponse:
    """Generate a website audit or no-website report."""
    return await SalesAssistantService(db).generate_audit(business_id)


@router.post("/businesses/{business_id}/proposal", response_model=ProposalResponse)
async def generate_proposal(
    business_id: int,
    db: Annotated[Session, Depends(get_db)],
) -> ProposalResponse:
    """Generate a professional proposal."""
    return await SalesAssistantService(db).generate_proposal(business_id)


@router.post("/proposal/pdf")
def proposal_pdf(
    payload: ProposalResponse,
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    """Export proposal content as a PDF."""
    pdf = SalesAssistantService(db).proposal_pdf(payload.content)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=leadforge-proposal.pdf"},
    )


@router.get("/insights", response_model=SalesInsightsResponse)
def sales_insights(db: Annotated[Session, Depends(get_db)]) -> SalesInsightsResponse:
    """Return CRM sales insights."""
    return SalesAssistantService(db).generate_sales_insights()


@router.post("/businesses/{business_id}/summary", response_model=AIGenerationResponse)
async def generate_summary(
    business_id: int,
    db: Annotated[Session, Depends(get_db)],
) -> AIGenerationResponse:
    """Generate a lead summary."""
    return await SalesAssistantService(db).generate_summary(business_id)


@router.post("/objection", response_model=AIGenerationResponse)
async def objection_replies(
    payload: ObjectionRequest, db: Annotated[Session, Depends(get_db)]
) -> AIGenerationResponse:
    """Generate objection-handling replies."""
    return await SalesAssistantService(db).generate_objection_replies(payload.objection)


@router.post("/businesses/{business_id}/conversation", response_model=AIGenerationResponse)
async def conversation_reply(
    business_id: int,
    payload: ConversationRequest,
    db: Annotated[Session, Depends(get_db)],
) -> AIGenerationResponse:
    """Generate contextual conversation reply."""
    return await SalesAssistantService(db).generate_conversation_reply(business_id, payload.message)


@router.get("/prompts", response_model=dict[str, str])
def list_prompts() -> dict[str, str]:
    """Return editable prompt templates."""
    return prompt_library.list_prompts()


@router.patch("/prompts/{key}", response_model=dict[str, str])
def update_prompt(key: str, payload: PromptUpdateRequest) -> dict[str, str]:
    """Update an editable prompt template."""
    return prompt_library.update_prompt(key, payload.template)


@router.get("/demo/templates", response_model=list[str])
def list_demo_templates() -> list[str]:
    """Return available demo website templates."""
    return TemplateEngine().list_templates()


@router.post(
    "/businesses/{business_id}/demo/generate",
    response_model=DemoJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def generate_demo_website(
    business_id: int,
    payload: DemoGenerateRequest,
    background_tasks: BackgroundTasks,
    manager: Annotated[DemoJobManager, Depends(get_demo_job_manager)],
) -> DemoJobResponse:
    """Start demo website generation in the background."""
    if payload.template not in TemplateEngine().list_templates():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown template")
    job = manager.create(business_id)
    background_tasks.add_task(run_demo_generation_job, job, manager, template=payload.template)
    return DemoJobResponse(**job.to_read().model_dump())


@router.get("/demo/jobs/{job_id}", response_model=DemoJobResponse)
def read_demo_job(
    job_id: str,
    manager: Annotated[DemoJobManager, Depends(get_demo_job_manager)],
) -> DemoJobResponse:
    """Return demo generation job status."""
    job = manager.get(job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Demo job not found")
    return DemoJobResponse(**job.to_read().model_dump())
