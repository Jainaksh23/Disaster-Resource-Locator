"""
routers/resources.py — Resource management endpoints.
"""
import uuid
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import get_current_user
from core.database import get_db
from models.user import User
from models.emergency_report import EmergencyReport
from models.resource import Resource
from schemas.resource import (
    ResourceCreate,
    ResourceListResponse,
    ResourceResponse,
    ResourceUpdate,
)
from services import geo_service

router = APIRouter(prefix="/api/v1/resources", tags=["resources"])
logger = logging.getLogger(__name__)


def haversine_sql(lat_col, lon_col, target_lat: float, target_lon: float):
    """SQLAlchemy expression for Haversine distance in kilometers."""
    return 6371 * func.acos(
        func.cos(func.radians(target_lat)) * func.cos(func.radians(lat_col)) *
        func.cos(func.radians(lon_col) - func.radians(target_lon)) +
        func.sin(func.radians(target_lat)) * func.sin(func.radians(lat_col))
    )


@router.post("/", response_model=ResourceResponse, status_code=status.HTTP_201_CREATED)
async def create_resource(
    payload: ResourceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResourceResponse:
    """Register a new emergency resource."""
    lat, lon = payload.latitude, payload.longitude
    if lat is None or lon is None:
        coords = await geo_service.geocode_location(payload.location_name)
        if coords:
            lat, lon = coords

    resource = Resource(
        **payload.model_dump(exclude={"latitude", "longitude"}),
        latitude=lat,
        longitude=lon,
    )
    db.add(resource)
    await db.flush()
    await db.refresh(resource)
    return ResourceResponse.model_validate(resource)


@router.get("/", response_model=ResourceListResponse)
async def list_resources(
    db: AsyncSession = Depends(get_db),
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    resource_type: str | None = None,
    status: str | None = None,
) -> ResourceListResponse:
    """List resources with optional filters."""
    filters = []
    if resource_type:
        filters.append(Resource.resource_type == resource_type)
    if status:
        filters.append(Resource.status == status)

    total: int = (
        await db.execute(select(func.count()).select_from(Resource).where(*filters))
    ).scalar_one()

    stmt = (
        select(Resource)
        .where(*filters)
        .order_by(Resource.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = (await db.execute(stmt)).scalars().all()

    return ResourceListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[ResourceResponse.model_validate(r) for r in rows],
    )


@router.get("/nearby/{report_id}", response_model=list[dict])
async def nearby_resources(
    report_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    max_km: Annotated[float, Query(gt=0, le=500)] = 100.0,
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    """Find nearby resources using SQL Haversine calculation."""
    report = await db.get(EmergencyReport, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if report.latitude is None or report.longitude is None:
        raise HTTPException(status_code=422, detail="Report has no geocoordinates")

    distance_col = haversine_sql(Resource.latitude, Resource.longitude, report.latitude, report.longitude)
    
    stmt = (
        select(Resource, distance_col.label("distance_km"))
        .where(
            Resource.status == "available",
            Resource.latitude.is_not(None),
            Resource.longitude.is_not(None),
            distance_col <= max_km
        )
        .order_by(distance_col.asc())
        .limit(50)
    )
    
    results = await db.execute(stmt)
    
    nearby = []
    for row in results.all():
        resource = row.Resource
        distance = row.distance_km
        nearby.append({
            "id": str(resource.id),
            "name": resource.name,
            "resource_type": resource.resource_type,
            "capacity": resource.capacity,
            "location_name": resource.location_name,
            "latitude": resource.latitude,
            "longitude": resource.longitude,
            "distance_km": round(float(distance), 2)
        })
        
    return nearby


@router.get("/{resource_id}", response_model=ResourceResponse)
async def get_resource(resource_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> ResourceResponse:
    resource = await db.get(Resource, resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    return ResourceResponse.model_validate(resource)


@router.patch("/{resource_id}", response_model=ResourceResponse)
async def update_resource(
    resource_id: uuid.UUID,
    payload: ResourceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResourceResponse:
    resource = await db.get(Resource, resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(resource, field, value)
    await db.flush()
    await db.refresh(resource)
    return ResourceResponse.model_validate(resource)


@router.delete("/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resource(
    resource_id: uuid.UUID, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    resource = await db.get(Resource, resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    await db.delete(resource)
