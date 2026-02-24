from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Optional

import ulid

from src.shipping_bc.shipment.domain.enums import (
    DestinationType,
    InvalidShipmentStatusTransitionError,
    ShipmentDirection,
    ShipmentStatus,
    VALID_TRANSITIONS,
)

MAX_ITEMS_PER_SHIPMENT = 20


@dataclass
class ShipmentItem:
    id: str
    shipment_id: str
    asset_id: str
    notes: Optional[str] = None

    @classmethod
    def create(
        cls,
        shipment_id: str,
        asset_id: str,
        notes: Optional[str] = None,
        id: Optional[str] = None,
    ) -> "ShipmentItem":
        return cls(
            id=id or str(ulid.new()),
            shipment_id=shipment_id,
            asset_id=asset_id,
            notes=notes,
        )


@dataclass
class Shipment:
    id: str
    company_id: str
    direction: ShipmentDirection
    destination_type: DestinationType
    status: ShipmentStatus
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
    items: list[ShipmentItem] = field(default_factory=list)

    @classmethod
    def create(
        cls,
        company_id: str,
        direction: ShipmentDirection,
        destination_type: DestinationType,
        destination_location_id: str,
        created_by: str,
        origin_location_id: Optional[str] = None,
        recipient_name: Optional[str] = None,
        recipient_user_id: Optional[str] = None,
        carrier: Optional[str] = None,
        service_level: Optional[str] = None,
        tracking_number: Optional[str] = None,
        tracking_url: Optional[str] = None,
        items_description: Optional[str] = None,
        internal_notes: Optional[str] = None,
        request_id: Optional[str] = None,
        po_id: Optional[str] = None,
        return_for_shipment_id: Optional[str] = None,
        notes: Optional[str] = None,
        items: Optional[list[ShipmentItem]] = None,
        id: Optional[str] = None,
    ) -> "Shipment":
        item_list = items or []
        if len(item_list) > MAX_ITEMS_PER_SHIPMENT:
            raise ValueError(
                f"Cannot create shipment with more than "
                f"{MAX_ITEMS_PER_SHIPMENT} items"
            )
        return cls(
            id=id or str(ulid.new()),
            company_id=company_id,
            direction=direction,
            destination_type=destination_type,
            status=ShipmentStatus.DRAFT,
            destination_location_id=destination_location_id,
            created_by=created_by,
            origin_location_id=origin_location_id,
            recipient_name=recipient_name,
            recipient_user_id=recipient_user_id,
            carrier=carrier,
            service_level=service_level,
            tracking_number=tracking_number,
            tracking_url=tracking_url,
            items_description=items_description,
            internal_notes=internal_notes,
            request_id=request_id,
            po_id=po_id,
            return_for_shipment_id=return_for_shipment_id,
            notes=notes,
            items=item_list,
        )

    def _transition(self, target: ShipmentStatus) -> None:
        allowed = VALID_TRANSITIONS.get(self.status, [])
        if target not in allowed:
            raise InvalidShipmentStatusTransitionError(
                self.status, target,
            )
        self.status = target

    def dispatch(self) -> None:
        if not self.carrier:
            raise ValueError(
                "Carrier is required to dispatch a shipment"
            )
        if not self.tracking_number:
            raise ValueError(
                "Tracking number is required to dispatch a shipment"
            )
        self._transition(ShipmentStatus.DISPATCHED)
        self.dispatched_at = datetime.now(UTC)

    def mark_in_transit(self) -> None:
        self._transition(ShipmentStatus.IN_TRANSIT)

    def deliver(self) -> None:
        self._transition(ShipmentStatus.DELIVERED)
        self.delivered_at = datetime.now(UTC)

    def fail(self, reason: str) -> None:
        self._transition(ShipmentStatus.FAILED)
        self.failure_reason = reason

    def cancel(self, reason: str) -> None:
        self._transition(ShipmentStatus.CANCELLED)
        self.cancellation_reason = reason

    def add_item(self, item: ShipmentItem) -> None:
        if self.status != ShipmentStatus.DRAFT:
            raise ValueError(
                "Items can only be modified while shipment is in DRAFT status"
            )
        if len(self.items) >= MAX_ITEMS_PER_SHIPMENT:
            raise ValueError(
                f"Cannot add more than {MAX_ITEMS_PER_SHIPMENT} items"
            )
        self.items.append(item)

    def remove_item(self, item_id: str) -> None:
        if self.status != ShipmentStatus.DRAFT:
            raise ValueError(
                "Items can only be modified while shipment is in DRAFT status"
            )
        self.items = [i for i in self.items if i.id != item_id]
