from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class CreateAssetRequest(BaseModel):
    type: str
    brand: str = Field(min_length=1, max_length=255)
    model: str = Field(min_length=1, max_length=255)
    serial_number: str = Field(min_length=1, max_length=255)
    purchase_date: Optional[date] = None
    warranty_expiration: Optional[date] = None
    notes: Optional[str] = None


class UpdateAssetRequest(BaseModel):
    brand: Optional[str] = Field(None, min_length=1, max_length=255)
    model: Optional[str] = Field(None, min_length=1, max_length=255)
    purchase_date: Optional[date] = None
    warranty_expiration: Optional[date] = None
    notes: Optional[str] = None


class AssignAssetRequest(BaseModel):
    user_id: str = Field(min_length=1)


class ChangeStatusRequest(BaseModel):
    status: str


class AssetResponse(BaseModel):
    id: str
    company_id: str
    type: str
    brand: str
    model: str
    serial_number: str
    status: str
    assigned_to: Optional[str] = None
    department_id: Optional[str] = None
    purchase_date: Optional[date] = None
    warranty_expiration: Optional[date] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class AssetEventResponse(BaseModel):
    id: str
    asset_id: str
    event_type: str
    data: dict
    performed_by: str
    created_at: Optional[datetime] = None


class ImportRowErrorResponse(BaseModel):
    row: int
    error: str


class ImportResponse(BaseModel):
    total: int
    successful: int
    failed: list[ImportRowErrorResponse]
