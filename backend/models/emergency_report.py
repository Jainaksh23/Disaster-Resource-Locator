"""
models/emergency_report.py — EmergencyReport ORM model.
Stores incoming emergency incidents with geo-coordinates and JSON fields.
"""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class EmergencyReport(Base):
    __tablename__ = "emergency_reports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # ── Classification ────────────────────────────────────────────────────────
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    severity_score: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")

    # ── Location ──────────────────────────────────────────────────────────────
    location_name: Mapped[str] = mapped_column(String(255), nullable=False)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)

    # ── Reporter ──────────────────────────────────────────────────────────────
    reporter_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    # ── AI Outputs ────────────────────────────────────────────────────────────
    structured_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    raw_gemini_output: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

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
        return f"<EmergencyReport {self.title} [Score: {self.severity_score}]>"
