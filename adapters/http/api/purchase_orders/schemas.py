from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class POItemRequest(BaseModel):
    description: str = Field(
        min_length=1, max_length=500,
    )
    asset_type: Optional[str] = None
    quantity: int = Field(ge=1)
    unit_cost_cents: int = Field(ge=0)
    notes: Optional[str] = None


class POCreateRequest(BaseModel):
    vendor_id: Optional[str] = None
    vendor_name: str = Field(
        min_length=1, max_length=200,
    )
    department_id: str = Field(min_length=1)
    items: list[POItemRequest] = Field(min_length=1)
    request_ids: list[str] = []
    notes: Optional[str] = None


class POUpdateRequest(BaseModel):
    vendor_id: Optional[str] = None
    vendor_name: str = Field(
        min_length=1, max_length=200,
    )
    department_id: str = Field(min_length=1)
    items: list[POItemRequest] = Field(min_length=1)
    request_ids: list[str] = []
    notes: Optional[str] = None


class RejectRequest(BaseModel):
    reason: str = Field(min_length=1)


class CancelRequest(BaseModel):
    reason: str = Field(min_length=1)


class ReceiveItemRequest(BaseModel):
    item_id: str = Field(min_length=1)
    received_quantity: int = Field(ge=1)
    create_asset: bool = False
    link_asset_id: Optional[str] = None
    location_id: Optional[str] = None


class ReceiveRequest(BaseModel):
    items: list[ReceiveItemRequest] = Field(
        min_length=1,
    )


class POItemResponse(BaseModel):
    id: str
    description: str
    asset_type: Optional[str] = None
    quantity: int
    unit_cost_cents: int
    total_cost_cents: int
    received_quantity: int = 0
    received_at: Optional[datetime] = None
    linked_asset_id: Optional[str] = None
    notes: Optional[str] = None


class POResponse(BaseModel):
    id: str
    company_id: str
    po_number: str
    vendor_id: Optional[str] = None
    vendor_name: str
    department_id: str
    status: str
    total_amount_cents: int
    currency: str
    notes: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    ordered_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None
    created_by: str
    items: list[POItemResponse]
    request_ids: list[str]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
