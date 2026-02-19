from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ProfileItemRequest(BaseModel):
    asset_type: str = Field(min_length=1)
    quantity: int = Field(default=1, ge=1, le=100)
    preferred_brand: Optional[str] = Field(
        default=None, max_length=100,
    )
    preferred_model: Optional[str] = Field(
        default=None, max_length=100,
    )
    min_ram_gb: Optional[int] = Field(
        default=None, ge=1,
    )
    min_storage_gb: Optional[int] = Field(
        default=None, ge=1,
    )


class CreateProfileRequest(BaseModel):
    department_id: str = Field(min_length=1)
    role: str = Field(min_length=1)
    items: list[ProfileItemRequest] = Field(
        min_length=1,
    )


class UpdateProfileRequest(BaseModel):
    items: list[ProfileItemRequest] = Field(
        min_length=1,
    )


class ProfileItemResponse(BaseModel):
    id: str
    asset_type: str
    quantity: int
    preferred_brand: Optional[str] = None
    preferred_model: Optional[str] = None
    min_ram_gb: Optional[int] = None
    min_storage_gb: Optional[int] = None


class ProfileResponse(BaseModel):
    id: str
    company_id: str
    department_id: str
    role: str
    is_active: bool
    items: list[ProfileItemResponse] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
