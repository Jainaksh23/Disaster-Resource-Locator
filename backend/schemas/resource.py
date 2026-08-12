"""
schemas/resource.py — Pydantic schemas for Resource endpoints.
"""
import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


ResourceType = Literal["hospital", "shelter", "bloodbank", "ngo", "fire_station", "police_station"]
ResourceStatus = Literal["available", "deployed", "maintenance", "unavailable"]


class ResourceBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    resource_type: ResourceType
    capacity: int = Field(default=1, ge=1)
    status: ResourceStatus = "available"
    location_name: str = Field(..., min_length=2, max_length=255)
    latitude: float | None = Field(None, ge=-90, le=90)
    longitude: float | None = Field(None, ge=-180, le=180)
    contact: str | None = Field(None, max_length=255)


class ResourceCreate(ResourceBase):
    pass


class ResourceUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=255)
    resource_type: ResourceType | None = None
    capacity: int | None = Field(None, ge=1)
    status: ResourceStatus | None = None
    location_name: str | None = Field(None, min_length=2, max_length=255)
    latitude: float | None = Field(None, ge=-90, le=90)
    longitude: float | None = Field(None, ge=-180, le=180)
    contact: str | None = Field(None, max_length=255)


class ResourceResponse(ResourceBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ResourceListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[ResourceResponse]
