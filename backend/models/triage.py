"""
models/triage.py — TriageCase ORM model.
Records individual victim triage assessments, optionally enriched by Gemini AI.
"""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class TriageCase(Base):
    __tablename__ = "triage_cases"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # ── Link to incident ──────────────────────────────────────────────────────
    report_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )

    # ── Patient info ──────────────────────────────────────────────────────────
    patient_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    age_estimate: Mapped[str | None] = mapped_column(String(50), nullable=True)
    gender: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # ── Triage classification (START protocol) ────────────────────────────────
    triage_color: Mapped[str] = mapped_column(String(20), nullable=False, default="green")
    # green (minor) | yellow (delayed) | red (immediate) | black (deceased/expectant)

    # ── Symptoms & assessment ─────────────────────────────────────────────────
    symptoms: Mapped[str] = mapped_column(Text, nullable=False)
    vital_signs: Mapped[str | None] = mapped_column(Text, nullable=True)
    # JSON string: {"pulse": 90, "resp_rate": 18, "gcs": 15}

    # ── AI recommendation ─────────────────────────────────────────────────────
    ai_recommendation: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_confidence: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # high | medium | low

    # ── Outcome ───────────────────────────────────────────────────────────────
    outcome: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # treated_on_site | transported | deceased | missing

    # ── Timestamps ────────────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<TriageCase {self.id} color={self.triage_color}>"
