"""
routers/sop.py — SOP Document management endpoints (for RAG).
"""
import uuid
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import get_current_user, require_admin
from core.database import get_db
from models.user import User
from models.sop_document import SOPDocument
from schemas.sop_document import (
    SOPDocumentCreate,
    SOPDocumentListResponse,
    SOPDocumentResponse,
    SOPDocumentUpdate,
)

router = APIRouter(prefix="/api/v1/sop", tags=["sop"])
logger = logging.getLogger(__name__)


@router.post("/", response_model=SOPDocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_sop(
    payload: SOPDocumentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> SOPDocumentResponse:
    """Create a new SOP document (Admin only)."""
    data = payload.model_dump()
    if data.get("source_url"):
        data["source_url"] = str(data["source_url"])
        
    doc = SOPDocument(**data)
    db.add(doc)
    await db.flush()
    await db.refresh(doc)
    return SOPDocumentResponse.model_validate(doc)


@router.get("/", response_model=SOPDocumentListResponse)
async def list_sops(
    db: AsyncSession = Depends(get_db),
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    category: str | None = None,
    current_user: User = Depends(get_current_user),
) -> SOPDocumentListResponse:
    """List SOP documents."""
    filters = []
    if category:
        filters.append(SOPDocument.category == category)

    total: int = (
        await db.execute(select(func.count()).select_from(SOPDocument).where(*filters))
    ).scalar_one()

    stmt = (
        select(SOPDocument)
        .where(*filters)
        .order_by(SOPDocument.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = (await db.execute(stmt)).scalars().all()

    return SOPDocumentListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[SOPDocumentResponse.model_validate(r) for r in rows],
    )


@router.get("/{doc_id}", response_model=SOPDocumentResponse)
async def get_sop(
    doc_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SOPDocumentResponse:
    doc = await db.get(SOPDocument, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="SOP Document not found")
    return SOPDocumentResponse.model_validate(doc)


@router.patch("/{doc_id}", response_model=SOPDocumentResponse)
async def update_sop(
    doc_id: uuid.UUID,
    payload: SOPDocumentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> SOPDocumentResponse:
    """Update SOP Document (Admin only)."""
    doc = await db.get(SOPDocument, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="SOP Document not found")

    data = payload.model_dump(exclude_unset=True)
    if data.get("source_url"):
        data["source_url"] = str(data["source_url"])

    for field, value in data.items():
        setattr(doc, field, value)
        
    await db.flush()
    await db.refresh(doc)
    return SOPDocumentResponse.model_validate(doc)


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sop(
    doc_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> None:
    """Delete SOP Document (Admin only)."""
    doc = await db.get(SOPDocument, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="SOP Document not found")
    await db.delete(doc)
