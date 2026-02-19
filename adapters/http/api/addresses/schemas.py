from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AddressCreateRequest(BaseModel):
    label: str
    street_line_1: str
    city: str
    state: str
    postal_code: str
    country: str = "US"
    street_line_2: Optional[str] = None
    recipient_name: Optional[str] = None
    phone: Optional[str] = None
    user_id: Optional[str] = None
    is_office: bool = False


class AddressUpdateRequest(BaseModel):
    label: Optional[str] = None
    street_line_1: Optional[str] = None
    street_line_2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    recipient_name: Optional[str] = None
    phone: Optional[str] = None
    user_id: Optional[str] = None
    is_office: Optional[bool] = None


class AddressResponse(BaseModel):
    id: str
    company_id: str
    label: str
    street_line_1: str
    street_line_2: Optional[str] = None
    city: str
    state: str
    postal_code: str
    country: str
    recipient_name: Optional[str] = None
    phone: Optional[str] = None
    user_id: Optional[str] = None
    is_office: bool
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
