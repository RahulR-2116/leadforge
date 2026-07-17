from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.business import BusinessStatus
from app.schemas.business import (
    BusinessCreate,
    BusinessDetail,
    BusinessList,
    BusinessRead,
    BusinessStats,
    BusinessStatusUpdate,
    BusinessUpdate,
    DemoCreate,
    DemoRead,
    FollowUpCreate,
    FollowUpRead,
    MessageCreate,
    MessageRead,
)
from app.services.businesses import (
    SortDirection,
    SortField,
    add_demo,
    add_follow_up,
    add_message,
    create_business,
    delete_business,
    export_businesses_csv,
    export_businesses_xlsx,
    get_business_or_404,
    get_business_stats,
    list_businesses,
    update_business,
    update_business_status,
)

router = APIRouter(prefix="/businesses", tags=["businesses"])


@router.get("", response_model=BusinessList)
def list_business_leads(
    db: Annotated[Session, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    search: str | None = None,
    category: str | None = None,
    city: str | None = None,
    state: str | None = None,
    has_website: bool | None = None,
    status_value: Annotated[BusinessStatus | None, Query(alias="status")] = None,
    sort_by: SortField = "created_at",
    sort_direction: SortDirection = "desc",
) -> BusinessList:
    """List business leads with search, filters, sorting, and pagination."""
    return list_businesses(
        db,
        page=page,
        page_size=page_size,
        search=search,
        category=category,
        city=city,
        state=state,
        has_website=has_website,
        status_value=status_value,
        sort_by=sort_by,
        sort_direction=sort_direction,
    )


@router.post("", response_model=BusinessDetail, status_code=status.HTTP_201_CREATED)
def create_business_lead(
    payload: BusinessCreate, db: Annotated[Session, Depends(get_db)]
) -> BusinessDetail:
    """Create a business lead."""
    return BusinessDetail.model_validate(create_business(db, payload))


@router.get("/stats", response_model=BusinessStats)
def read_business_stats(db: Annotated[Session, Depends(get_db)]) -> BusinessStats:
    """Return lead management dashboard statistics."""
    return get_business_stats(db)


@router.get("/export")
def export_business_leads(
    db: Annotated[Session, Depends(get_db)],
    format_value: Annotated[Literal["csv", "xlsx"], Query(alias="format")] = "csv",
) -> Response:
    """Export all business leads as CSV or Excel."""
    if format_value == "xlsx":
        return Response(
            content=export_businesses_xlsx(db),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=leadforge-businesses.xlsx"},
        )
    return Response(
        content=export_businesses_csv(db),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=leadforge-businesses.csv"},
    )


@router.post("/bulk/status", response_model=list[BusinessRead])
def bulk_update_status(
    payload: BusinessStatusUpdate,
    ids: Annotated[list[int], Query(min_length=1)],
    db: Annotated[Session, Depends(get_db)],
) -> list[BusinessRead]:
    """Update status for multiple business leads."""
    return [
        BusinessRead.model_validate(update_business_status(db, business_id, payload.status))
        for business_id in ids
    ]


@router.delete("/bulk", status_code=status.HTTP_204_NO_CONTENT)
def bulk_delete_business_leads(
    ids: Annotated[list[int], Query(min_length=1)], db: Annotated[Session, Depends(get_db)]
) -> Response:
    """Delete multiple business leads."""
    for business_id in ids:
        delete_business(db, business_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{business_id}", response_model=BusinessDetail)
def read_business_lead(business_id: int, db: Annotated[Session, Depends(get_db)]) -> BusinessDetail:
    """Return a business lead with CRM history."""
    return BusinessDetail.model_validate(get_business_or_404(db, business_id))


@router.patch("/{business_id}", response_model=BusinessDetail)
def update_business_lead(
    business_id: int, payload: BusinessUpdate, db: Annotated[Session, Depends(get_db)]
) -> BusinessDetail:
    """Update a business lead."""
    return BusinessDetail.model_validate(update_business(db, business_id, payload))


@router.delete("/{business_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_business_lead(business_id: int, db: Annotated[Session, Depends(get_db)]) -> Response:
    """Delete a business lead."""
    delete_business(db, business_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/{business_id}/status", response_model=BusinessRead)
def update_business_lead_status(
    business_id: int, payload: BusinessStatusUpdate, db: Annotated[Session, Depends(get_db)]
) -> BusinessRead:
    """Update a business lead status."""
    return BusinessRead.model_validate(update_business_status(db, business_id, payload.status))


@router.post(
    "/{business_id}/follow-ups",
    response_model=FollowUpRead,
    status_code=status.HTTP_201_CREATED,
)
def create_follow_up(
    business_id: int, payload: FollowUpCreate, db: Annotated[Session, Depends(get_db)]
) -> FollowUpRead:
    """Add a follow-up to a business lead."""
    return FollowUpRead.model_validate(add_follow_up(db, business_id, payload))


@router.post("/{business_id}/demos", response_model=DemoRead, status_code=status.HTTP_201_CREATED)
def create_demo(
    business_id: int, payload: DemoCreate, db: Annotated[Session, Depends(get_db)]
) -> DemoRead:
    """Add demo history to a business lead."""
    return DemoRead.model_validate(add_demo(db, business_id, payload))


@router.post(
    "/{business_id}/messages",
    response_model=MessageRead,
    status_code=status.HTTP_201_CREATED,
)
def create_message(
    business_id: int, payload: MessageCreate, db: Annotated[Session, Depends(get_db)]
) -> MessageRead:
    """Add message history to a business lead."""
    return MessageRead.model_validate(add_message(db, business_id, payload))
