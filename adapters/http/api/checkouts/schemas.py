from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CreateCheckoutRequest(BaseModel):
    user_id: str
    condition_out: str
    condition_out_notes: Optional[str] = None
    notes_out: Optional[str] = None


class CheckinRequest(BaseModel):
    condition_in: str
    condition_in_notes: Optional[str] = None
    notes_in: Optional[str] = None


class CancelCheckoutRequest(BaseModel):
    reason: Optional[str] = None


class CheckoutResponse(BaseModel):
    id: str
    asset_id: str
    user_id: str
    checked_out_by: str
    checked_out_at: datetime
    condition_out: str
    condition_out_notes: Optional[str] = None
    notes_out: Optional[str] = None
    accepted_at: Optional[datetime] = None
    checked_in_at: Optional[datetime] = None
    checked_in_by: Optional[str] = None
    condition_in: Optional[str] = None
    condition_in_notes: Optional[str] = None
    notes_in: Optional[str] = None
    cancelled_at: Optional[datetime] = None
    cancelled_by: Optional[str] = None
    cancel_reason: Optional[str] = None
    maintenance_id: Optional[str] = None
    auto_assigned: bool = False
    status: str
    created_at: Optional[datetime] = None


class MyEquipmentCheckoutResponse(BaseModel):
    id: str
    asset_id: str
    condition_out: str
    checked_out_at: datetime
    accepted_at: Optional[datetime] = None
    status: str
