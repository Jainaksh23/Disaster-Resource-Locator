"""
routers/triage.py — Triage case management endpoints.
POST   /api/v1/triage/          — create triage case (optionally AI-classified)
GET    /api/v1/triage/           — list cases (paginated, filterable by color/report)
GET    /api/v1/triage/{id}       — get single case
PATCH  /api/v1/triage/{id}       — update case (outcome, manual override)
DELETE /api/v1/triage/{id}       — delete case
POST   /api/v1/triage/{id}/reclassify — re-run Gemini classification
"""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import get_current_user
from core.database import get_db
from models.user import User
from models.triage import TriageCase
from schemas.triage import (
    TriageCaseCreate,
    TriageCaseResponse,
    TriageCaseUpdate,
    TriageListResponse,
)
from services import gemini_service

router = APIRouter(prefix="/api/v1/triage", tags=["triage"])


@router.post("/", response_model=TriageCaseResponse, status_code=status.HTTP_201_CREATED)
async def create_triage_case(
    payload: TriageCaseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TriageCaseResponse:
    """
    Create a triage case. If auto_classify=True (default), Gemini will
    determine the triage color and recommendation from symptoms + vitals.
    """
    ai_result = {}
    if payload.auto_classify:
        ai_result = await gemini_service.classify_triage(
            symptoms=payload.symptoms,
            vital_signs=payload.vital_signs,
        )

    case_data = payload.model_dump(exclude={"auto_classify"})
    if ai_result:
        case_data["triage_color"] = ai_result.get("triage_color", case_data["triage_color"])
        case_data["ai_recommendation"] = ai_result.get("recommendation")
        case_data["ai_confidence"] = ai_result.get("confidence")

    case = TriageCase(**case_data)
    db.add(case)
    await db.flush()
    await db.refresh(case)
    return TriageCaseResponse.model_validate(case)


@router.get("/", response_model=TriageListResponse)
async def list_triage_cases(
    db: AsyncSession = Depends(get_db),
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    triage_color: str | None = None,
    report_id: uuid.UUID | None = None,
    current_user: User = Depends(get_current_user),
) -> TriageListResponse:
    filters = []
    if triage_color:
        filters.append(TriageCase.triage_color == triage_color)
    if report_id:
        filters.append(TriageCase.report_id == report_id)

    total: int = (
        await db.execute(select(func.count()).select_from(TriageCase).where(*filters))
    ).scalar_one()

    stmt = (
        select(TriageCase)
        .where(*filters)
        .order_by(TriageCase.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = (await db.execute(stmt)).scalars().all()

    return TriageListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[TriageCaseResponse.model_validate(c) for c in rows],
    )


@router.get("/{case_id}", response_model=TriageCaseResponse)
async def get_triage_case(
    case_id: uuid.UUID, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TriageCaseResponse:
    case = await db.get(TriageCase, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Triage case not found")
    return TriageCaseResponse.model_validate(case)


@router.patch("/{case_id}", response_model=TriageCaseResponse)
async def update_triage_case(
    case_id: uuid.UUID,
    payload: TriageCaseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TriageCaseResponse:
    case = await db.get(TriageCase, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Triage case not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(case, field, value)
    await db.flush()
    await db.refresh(case)
    return TriageCaseResponse.model_validate(case)


@router.post("/{case_id}/reclassify", response_model=TriageCaseResponse)
async def reclassify_triage_case(
    case_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TriageCaseResponse:
    """Re-run Gemini classification on an existing triage case."""
    case = await db.get(TriageCase, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Triage case not found")

    ai_result = await gemini_service.classify_triage(
        symptoms=case.symptoms,
        vital_signs=case.vital_signs,
    )
    case.triage_color = ai_result.get("triage_color", case.triage_color)
    case.ai_recommendation = ai_result.get("recommendation")
    case.ai_confidence = ai_result.get("confidence")

    await db.flush()
    await db.refresh(case)
    return TriageCaseResponse.model_validate(case)


@router.delete("/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_triage_case(
    case_id: uuid.UUID, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    case = await db.get(TriageCase, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Triage case not found")
    await db.delete(case)
