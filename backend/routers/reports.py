"""
routers/reports.py — Emergency report CRUD endpoints.
"""
import uuid
import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import get_current_user
from core.database import get_db
from models.user import User
from models.emergency_report import EmergencyReport
from schemas.emergency_report import (
    EmergencyReportCreate,
    EmergencyReportListResponse,
    EmergencyReportResponse,
    EmergencyReportUpdate,
)
from services import gemini_service, geo_service, triage_service

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])
logger = logging.getLogger(__name__)


@router.post("/", response_model=EmergencyReportResponse, status_code=status.HTTP_201_CREATED)
async def create_report(
    payload: EmergencyReportCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EmergencyReportResponse:
    """Create an emergency report."""
    lat, lon = payload.latitude, payload.longitude
    if lat is None or lon is None:
        coords = await geo_service.geocode_location(payload.location_name)
        if coords:
            lat, lon = coords

    # Calculate real report-level severity score using Gemini + rule-based fallback
    triage_result = await triage_service.calculate_report_severity(
        title=payload.title, 
        description=payload.description
    )

    category = triage_result["structured_data"]["disaster_type"]
    
    # Retrieve SOP recommendations using RAG (Temporarily Disabled)
    # rag_query = f"{category}: {payload.description}"
    # suggested_actions = await rag_service.query_index(rag_query, top_k=3)
    suggested_actions = []

    report = EmergencyReport(
        **payload.model_dump(exclude={"latitude", "longitude", "category", "severity_score"}),
        latitude=lat,
        longitude=lon,
        reporter_id=current_user.id,
        category=category,
        severity_score=triage_result["severity_score"],
        structured_data=triage_result["structured_data"],
        raw_gemini_output=triage_result["raw_gemini_output"],
    )
    db.add(report)
    await db.flush()
    await db.refresh(report)
    
    # Construct response and inject RAG suggestions dynamically
    # (Since they are meant to guide responders, we can serve them directly or save to DB. 
    # For now, we inject into the response model).
    response = EmergencyReportResponse.model_validate(report)
    response.suggested_actions = suggested_actions
    return response


@router.get("/", response_model=EmergencyReportListResponse)
async def list_reports(
    db: AsyncSession = Depends(get_db),
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    category: str | None = None,
    status: str | None = None,
) -> EmergencyReportListResponse:
    """List reports with optional filters and pagination."""
    filters = []
    if category:
        filters.append(EmergencyReport.category == category)
    if status:
        filters.append(EmergencyReport.status == status)

    count_stmt = select(func.count()).select_from(EmergencyReport).where(*filters)
    total: int = (await db.execute(count_stmt)).scalar_one()

    stmt = (
        select(EmergencyReport)
        .where(*filters)
        .order_by(EmergencyReport.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = (await db.execute(stmt)).scalars().all()

    return EmergencyReportListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[EmergencyReportResponse.model_validate(r) for r in rows],
    )


@router.get("/{report_id}", response_model=EmergencyReportResponse)
async def get_report(report_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> EmergencyReportResponse:
    """Fetch a single report by ID."""
    report = await db.get(EmergencyReport, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return EmergencyReportResponse.model_validate(report)


@router.patch("/{report_id}", response_model=EmergencyReportResponse)
async def update_report(
    report_id: uuid.UUID,
    payload: EmergencyReportUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EmergencyReportResponse:
    """Partially update a report."""
    report = await db.get(EmergencyReport, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(report, field, value)

    await db.flush()
    await db.refresh(report)
    return EmergencyReportResponse.model_validate(report)


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
    report_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a report."""
    report = await db.get(EmergencyReport, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    await db.delete(report)
