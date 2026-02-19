from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class VendorCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    contact_email: Optional[str] = Field(
        default=None, max_length=254,
    )
    phone: Optional[str] = Field(
        default=None, max_length=50,
    )
    address: Optional[str] = None
    notes: Optional[str] = None


class VendorUpdateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    contact_email: Optional[str] = Field(
        default=None, max_length=254,
    )
    phone: Optional[str] = Field(
        default=None, max_length=50,
    )
    address: Optional[str] = None
    notes: Optional[str] = None


class VendorResponse(BaseModel):
    id: str
    company_id: str
    name: str
    contact_email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
