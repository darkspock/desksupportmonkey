from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CreateShipmentRequest(BaseModel):
    direction: str
    destination_type: str
    destination_location_id: str
    asset_ids: list[str]
    origin_location_id: Optional[str] = None
    recipient_name: Optional[str] = None
    recipient_user_id: Optional[str] = None
    carrier: Optional[str] = None
    service_level: Optional[str] = None
    tracking_number: Optional[str] = None
    tracking_url: Optional[str] = None
    items_description: Optional[str] = None
    internal_notes: Optional[str] = None
    request_id: Optional[str] = None
    po_id: Optional[str] = None
    notes: Optional[str] = None


class DispatchShipmentRequest(BaseModel):
    carrier: Optional[str] = None
    tracking_number: Optional[str] = None
    tracking_url: Optional[str] = None


class FailShipmentRequest(BaseModel):
    reason: str


class CancelShipmentRequest(BaseModel):
    reason: str


class DeliverShipmentRequest(BaseModel):
    notes: Optional[str] = None


class UpdateShipmentRequest(BaseModel):
    carrier: Optional[str] = None
    service_level: Optional[str] = None
    tracking_number: Optional[str] = None
    tracking_url: Optional[str] = None
    items_description: Optional[str] = None
    internal_notes: Optional[str] = None
    notes: Optional[str] = None


class CreateReturnRequest(BaseModel):
    destination_location_id: str
    asset_ids: list[str]
    carrier: Optional[str] = None
    tracking_number: Optional[str] = None
    notes: Optional[str] = None


class ModifyItemsRequest(BaseModel):
    add_asset_ids: list[str] = []
    remove_item_ids: list[str] = []


class ShipmentItemResponse(BaseModel):
    id: str
    shipment_id: str
    asset_id: str
    notes: Optional[str] = None


class ShipmentResponse(BaseModel):
    id: str
    company_id: str
    direction: str
    destination_type: str
    status: str
    destination_location_id: str
    created_by: str
    origin_location_id: Optional[str] = None
    recipient_name: Optional[str] = None
    recipient_user_id: Optional[str] = None
    carrier: Optional[str] = None
    service_level: Optional[str] = None
    tracking_number: Optional[str] = None
    tracking_url: Optional[str] = None
    items_description: Optional[str] = None
    internal_notes: Optional[str] = None
    request_id: Optional[str] = None
    po_id: Optional[str] = None
    return_for_shipment_id: Optional[str] = None
    notes: Optional[str] = None
    failure_reason: Optional[str] = None
    cancellation_reason: Optional[str] = None
    dispatched_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    items: list[ShipmentItemResponse] = []
    item_count: int = 0


class ShipmentDashboardResponse(BaseModel):
    active_by_status: dict[str, int]
    recent_deliveries: list[ShipmentResponse]
    failed_count: int
