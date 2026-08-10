"""
routers/dashboard.py — Aggregated statistics for the operational dashboard.
"""
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import get_current_user
from core.database import get_db
from models.user import User
from models.emergency_report import EmergencyReport
from models.resource import Resource
from models.triage import TriageCase

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


@router.get("/stats")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Returns aggregated counts for the operational dashboard.
    """
    # ── Report stats ──────────────────────────────────────────────────────────
    total_reports: int = (
        await db.execute(select(func.count()).select_from(EmergencyReport))
    ).scalar_one()

    active_reports: int = (
        await db.execute(
            select(func.count()).select_from(EmergencyReport).where(EmergencyReport.status == "active")
        )
    ).scalar_one()

    resolved_reports: int = (
        await db.execute(
            select(func.count())
            .select_from(EmergencyReport)
            .where(EmergencyReport.status == "resolved")
        )
    ).scalar_one()

    # Severity breakdown
    severity_rows = (
        await db.execute(
            select(EmergencyReport.severity_score, func.count().label("count"))
            .group_by(EmergencyReport.severity_score)
        )
    ).all()
    reports_by_severity = {row.severity_score: row.count for row in severity_rows}

    # Category breakdown
    category_rows = (
        await db.execute(
            select(EmergencyReport.category, func.count().label("count"))
            .group_by(EmergencyReport.category)
        )
    ).all()
    reports_by_category = {row.category: row.count for row in category_rows}

    # ── Resource stats ────────────────────────────────────────────────────────
    total_resources: int = (
        await db.execute(select(func.count()).select_from(Resource))
    ).scalar_one()

    available_resources: int = (
        await db.execute(
            select(func.count()).select_from(Resource).where(Resource.status == "available")
        )
    ).scalar_one()

    deployed_resources: int = (
        await db.execute(
            select(func.count()).select_from(Resource).where(Resource.status == "deployed")
        )
    ).scalar_one()

    # ── Triage stats ──────────────────────────────────────────────────────────
    triage_rows = (
        await db.execute(
            select(TriageCase.triage_color, func.count().label("count"))
            .group_by(TriageCase.triage_color)
        )
    ).all()
    triage_by_color = {row.triage_color: row.count for row in triage_rows}

    total_patients: int = sum(triage_by_color.values())

    return {
        "reports": {
            "total": total_reports,
            "active": active_reports,
            "resolved": resolved_reports,
            "by_severity": reports_by_severity,
            "by_category": reports_by_category,
        },
        "resources": {
            "total": total_resources,
            "available": available_resources,
            "deployed": deployed_resources,
        },
        "triage": {
            "total_patients": total_patients,
            "by_color": triage_by_color,
        },
    }


@router.get("/map-pins")
async def get_map_pins(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    """
    Lightweight list of active report map pins.
    """
    stmt = (
        select(
            EmergencyReport.id,
            EmergencyReport.title,
            EmergencyReport.category,
            EmergencyReport.severity_score,
            EmergencyReport.status,
            EmergencyReport.latitude,
            EmergencyReport.longitude,
            EmergencyReport.location_name,
        )
        .where(
            EmergencyReport.latitude.isnot(None),
            EmergencyReport.longitude.isnot(None),
        )
        .order_by(EmergencyReport.created_at.desc())
    )
    rows = (await db.execute(stmt)).all()

    return [
        {
            "id": str(row.id),
            "title": row.title,
            "category": row.category,
            "severity_score": row.severity_score,
            "status": row.status,
            "latitude": row.latitude,
            "longitude": row.longitude,
            "location_name": row.location_name,
        }
        for row in rows
    ]
