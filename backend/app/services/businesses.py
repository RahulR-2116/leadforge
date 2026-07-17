from __future__ import annotations

import csv
from io import BytesIO, StringIO
from math import ceil
from typing import Any, Literal

from fastapi import HTTPException, status
from openpyxl import Workbook
from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.business import Business, BusinessStatus
from app.models.demo import Demo
from app.models.follow_up import FollowUp
from app.models.message import Message
from app.schemas.business import (
    BusinessCreate,
    BusinessList,
    BusinessRead,
    BusinessStats,
    BusinessUpdate,
    DemoCreate,
    FollowUpCreate,
    MessageCreate,
    normalize_url,
)

SortField = Literal[
    "business_name",
    "category",
    "city",
    "state",
    "status",
    "created_at",
    "updated_at",
    "rating",
    "review_count",
]
SortDirection = Literal["asc", "desc"]

SORT_COLUMNS: dict[str, Any] = {
    "business_name": Business.business_name,
    "category": Business.category,
    "city": Business.city,
    "state": Business.state,
    "status": Business.status,
    "created_at": Business.created_at,
    "updated_at": Business.updated_at,
    "rating": Business.rating,
    "review_count": Business.review_count,
}

EXPORT_HEADERS = [
    "id",
    "business_name",
    "category",
    "phone_number",
    "email",
    "city",
    "state",
    "country",
    "website",
    "has_website",
    "status",
    "rating",
    "review_count",
    "notes",
]


def _business_payload(payload: BusinessCreate | BusinessUpdate) -> dict[str, Any]:
    """Convert validated payloads into database-safe values."""
    data = payload.model_dump(exclude_unset=True)
    for key in ("website", "google_maps_url", "justdial_url"):
        if key in data:
            data[key] = normalize_url(data[key])
    if data.get("website") and "has_website" not in data:
        data["has_website"] = True
    return data


def _base_query() -> Select[tuple[Business]]:
    """Return a business query with detail relationships eager-loaded."""
    return select(Business).options(
        selectinload(Business.follow_ups),
        selectinload(Business.demos),
        selectinload(Business.messages),
    )


def get_business_or_404(db: Session, business_id: int) -> Business:
    """Return a business lead or raise a 404 API error."""
    business = db.scalar(_base_query().where(Business.id == business_id))
    if business is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found")
    return business


def ensure_business_is_unique(
    db: Session,
    *,
    business_name: str | None,
    phone_number: str | None,
    exclude_business_id: int | None = None,
) -> None:
    """Prevent duplicate leads by phone number or exact normalized business name."""
    conditions = []
    if phone_number:
        conditions.append(Business.phone_number == phone_number)
    if business_name:
        conditions.append(func.lower(Business.business_name) == business_name.strip().lower())
    if not conditions:
        return

    statement = select(Business).where(or_(*conditions))
    if exclude_business_id is not None:
        statement = statement.where(Business.id != exclude_business_id)
    duplicate = db.scalar(statement.limit(1))

    if duplicate is not None and phone_number and duplicate.phone_number == phone_number:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A business with this phone number already exists",
        )
    if duplicate is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A business with this name already exists",
        )


def create_business(db: Session, payload: BusinessCreate) -> Business:
    """Create a business lead after duplicate validation."""
    data = _business_payload(payload)
    ensure_business_is_unique(
        db, business_name=data.get("business_name"), phone_number=data.get("phone_number")
    )
    business = Business(**data)
    db.add(business)
    db.commit()
    db.refresh(business)
    return get_business_or_404(db, business.id)


def update_business(db: Session, business_id: int, payload: BusinessUpdate) -> Business:
    """Update a business lead."""
    business = get_business_or_404(db, business_id)
    data = _business_payload(payload)
    ensure_business_is_unique(
        db,
        business_name=data.get("business_name"),
        phone_number=data.get("phone_number"),
        exclude_business_id=business.id,
    )
    for field, value in data.items():
        setattr(business, field, value)
    db.commit()
    db.refresh(business)
    return get_business_or_404(db, business.id)


def update_business_status(db: Session, business_id: int, status_value: BusinessStatus) -> Business:
    """Update only the lifecycle status for a business lead."""
    business = get_business_or_404(db, business_id)
    business.status = status_value
    db.commit()
    db.refresh(business)
    return business


def delete_business(db: Session, business_id: int) -> None:
    """Delete a business lead and its CRM history."""
    business = get_business_or_404(db, business_id)
    db.delete(business)
    db.commit()


def list_businesses(
    db: Session,
    *,
    page: int,
    page_size: int,
    search: str | None,
    category: str | None,
    city: str | None,
    state: str | None,
    has_website: bool | None,
    status_value: BusinessStatus | None,
    sort_by: SortField,
    sort_direction: SortDirection,
) -> BusinessList:
    """Return filtered, sorted, paginated business leads."""
    statement = select(Business)

    if search:
        term = f"%{search.strip().lower()}%"
        statement = statement.where(
            or_(
                func.lower(Business.business_name).like(term),
                func.lower(Business.phone_number).like(term),
                func.lower(Business.category).like(term),
                func.lower(Business.city).like(term),
                func.lower(Business.state).like(term),
            )
        )
    if category:
        statement = statement.where(func.lower(Business.category) == category.strip().lower())
    if city:
        statement = statement.where(func.lower(Business.city) == city.strip().lower())
    if state:
        statement = statement.where(func.lower(Business.state) == state.strip().lower())
    if has_website is not None:
        statement = statement.where(Business.has_website.is_(has_website))
    if status_value is not None:
        statement = statement.where(Business.status == status_value)

    total = db.scalar(select(func.count()).select_from(statement.subquery())) or 0
    sort_column = SORT_COLUMNS[sort_by]
    order_clause = sort_column.desc() if sort_direction == "desc" else sort_column.asc()
    rows = db.scalars(
        statement.order_by(order_clause).offset((page - 1) * page_size).limit(page_size)
    ).all()

    return BusinessList(
        items=[BusinessRead.model_validate(row) for row in rows],
        total=total,
        page=page,
        page_size=page_size,
        pages=ceil(total / page_size) if total else 0,
    )


def add_follow_up(db: Session, business_id: int, payload: FollowUpCreate) -> FollowUp:
    """Create follow-up history for a business lead."""
    get_business_or_404(db, business_id)
    follow_up = FollowUp(business_id=business_id, **payload.model_dump())
    db.add(follow_up)
    db.commit()
    db.refresh(follow_up)
    return follow_up


def add_demo(db: Session, business_id: int, payload: DemoCreate) -> Demo:
    """Create demo history for a business lead."""
    get_business_or_404(db, business_id)
    data = payload.model_dump()
    data["demo_url"] = normalize_url(data.get("demo_url"))
    data["video_url"] = normalize_url(data.get("video_url"))
    demo = Demo(business_id=business_id, **data)
    db.add(demo)
    db.commit()
    db.refresh(demo)
    return demo


def add_message(db: Session, business_id: int, payload: MessageCreate) -> Message:
    """Create message history for a business lead."""
    get_business_or_404(db, business_id)
    message = Message(business_id=business_id, **payload.model_dump())
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def get_business_stats(db: Session) -> BusinessStats:
    """Return lead management metrics for the dashboard."""
    total = db.scalar(select(func.count(Business.id))) or 0

    def count_status(*statuses: BusinessStatus) -> int:
        return db.scalar(select(func.count(Business.id)).where(Business.status.in_(statuses))) or 0

    return BusinessStats(
        total_businesses=total,
        contacted=count_status(
            BusinessStatus.CONTACTED,
            BusinessStatus.REPLIED,
            BusinessStatus.DEMO_REQUESTED,
            BusinessStatus.DEMO_SENT,
            BusinessStatus.NEGOTIATING,
            BusinessStatus.CLIENT,
        ),
        replies=count_status(
            BusinessStatus.REPLIED,
            BusinessStatus.DEMO_REQUESTED,
            BusinessStatus.DEMO_SENT,
            BusinessStatus.NEGOTIATING,
            BusinessStatus.CLIENT,
        ),
        demos_sent=count_status(
            BusinessStatus.DEMO_SENT,
            BusinessStatus.NEGOTIATING,
            BusinessStatus.CLIENT,
        ),
        clients_won=count_status(BusinessStatus.CLIENT),
        lost=count_status(BusinessStatus.LOST),
    )


def _export_rows(db: Session) -> list[dict[str, Any]]:
    """Return all businesses as primitive dictionaries for exports."""
    businesses = db.scalars(select(Business).order_by(Business.business_name.asc())).all()
    return [
        {
            "id": business.id,
            "business_name": business.business_name,
            "category": business.category,
            "phone_number": business.phone_number,
            "email": business.email,
            "city": business.city,
            "state": business.state,
            "country": business.country,
            "website": business.website,
            "has_website": business.has_website,
            "status": business.status.value,
            "rating": business.rating,
            "review_count": business.review_count,
            "notes": business.notes,
        }
        for business in businesses
    ]


def export_businesses_csv(db: Session) -> str:
    """Return a CSV export of all businesses."""
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=EXPORT_HEADERS)
    writer.writeheader()
    writer.writerows(_export_rows(db))
    return output.getvalue()


def export_businesses_xlsx(db: Session) -> bytes:
    """Return an XLSX export of all businesses."""
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Businesses"
    sheet.append(EXPORT_HEADERS)
    for row in _export_rows(db):
        sheet.append([row[header] for header in EXPORT_HEADERS])

    output = BytesIO()
    workbook.save(output)
    return output.getvalue()
