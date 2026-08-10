"""
schemas/emergency_report.py — Pydantic schemas for EmergencyReport endpoints.
"""
import uuid
from datetime import datetime
from typing import Literal, Any

from pydantic import BaseModel, Field


SeverityScore = Field(..., ge=1, le=5) # 1-5 scale
ReportStatus = Literal["active", "contained", "resolved", "false_alarm"]


class EmergencyReportBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    description: str = Field(..., min_length=10)
    category: str = Field(..., min_length=2, max_length=100)
    severity_score: int = Field(default=1, ge=1, le=5)
    status: ReportStatus = "active"
    location_name: str = Field(..., min_length=2, max_length=255)
    latitude: float | None = Field(None, ge=-90, le=90)
    longitude: float | None = Field(None, ge=-180, le=180)


class EmergencyReportCreate(EmergencyReportBase):
    pass


class EmergencyReportUpdate(BaseModel):
    title: str | None = Field(None, min_length=3, max_length=255)
    description: str | None = None
    category: str | None = Field(None, min_length=2, max_length=100)
    severity_score: int | None = Field(None, ge=1, le=5)
    status: ReportStatus | None = None
    location_name: str | None = Field(None, min_length=2, max_length=255)
    latitude: float | None = Field(None, ge=-90, le=90)
    longitude: float | None = Field(None, ge=-180, le=180)
    structured_data: dict[str, Any] | None = None


class EmergencyReportResponse(EmergencyReportBase):
    id: uuid.UUID
    reporter_id: uuid.UUID | None
    structured_data: dict[str, Any] | None
    raw_gemini_output: dict[str, Any] | None
    suggested_actions: list[dict[str, Any]] | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EmergencyReportListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[EmergencyReportResponse]
