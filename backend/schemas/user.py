"""
schemas/user.py — Pydantic schemas for User endpoints.
"""
import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


UserRole = Literal["citizen", "admin", "responder"]


class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=255)
    role: UserRole = "citizen"


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
    # Role is always "citizen" on public signup — admin accounts are seeded only
    role: UserRole = Field(default="citizen", init=False)


class UserUpdate(BaseModel):
    full_name: str | None = Field(None, min_length=2, max_length=255)
    role: UserRole | None = None
    is_active: bool | None = None


class UserResponse(UserBase):
    id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Auth schemas ──────────────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
