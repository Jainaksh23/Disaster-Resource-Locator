"""
schemas/sop_document.py — Pydantic schemas for SOPDocument endpoints.
"""
import uuid
from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl


class SOPDocumentBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    category: str = Field(..., min_length=2, max_length=100)
    content: str = Field(..., min_length=10)
    source_url: HttpUrl | None = None


class SOPDocumentCreate(SOPDocumentBase):
    pass


class SOPDocumentUpdate(BaseModel):
    title: str | None = Field(None, min_length=3, max_length=255)
    category: str | None = Field(None, min_length=2, max_length=100)
    content: str | None = Field(None, min_length=10)
    source_url: HttpUrl | None = None


class SOPDocumentResponse(SOPDocumentBase):
    id: uuid.UUID
    source_url: str | None = None # Convert HttpUrl to string on output
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SOPDocumentListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[SOPDocumentResponse]
