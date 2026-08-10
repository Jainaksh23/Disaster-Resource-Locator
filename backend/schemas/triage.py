"""
schemas/triage.py — Pydantic schemas for TriageCase endpoints.
"""
import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


TriageColor = Literal["green", "yellow", "red", "black"]
AiConfidence = Literal["high", "medium", "low"]
TriageOutcome = Literal["treated_on_site", "transported", "deceased", "missing"]


class TriageBase(BaseModel):
    report_id: uuid.UUID | None = None
    patient_name: str | None = Field(None, max_length=255)
    age_estimate: str | None = Field(None, max_length=50)
    gender: str | None = Field(None, max_length=50)
    triage_color: TriageColor = "green"
    symptoms: str = Field(..., min_length=5)
    vital_signs: str | None = None  # JSON string


class TriageCaseCreate(TriageBase):
    """
    If triage_color is not provided, the Gemini service will classify
    based on symptoms and vital_signs.
    """
    auto_classify: bool = Field(
        default=True,
        description="Use Gemini AI to classify triage color from symptoms",
    )


class TriageCaseUpdate(BaseModel):
    triage_color: TriageColor | None = None
    vital_signs: str | None = None
    outcome: TriageOutcome | None = None
    ai_recommendation: str | None = None
    ai_confidence: AiConfidence | None = None


class TriageCaseResponse(TriageBase):
    id: uuid.UUID
    ai_recommendation: str | None
    ai_confidence: AiConfidence | None
    outcome: TriageOutcome | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TriageListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[TriageCaseResponse]
