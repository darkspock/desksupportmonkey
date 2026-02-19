from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Optional

import ulid

from src.procurement_bc.purchase_order.domain.enums import (
    InvalidPOStatusTransitionError,
    PurchaseOrderStatus,
    VALID_TRANSITIONS,
)


@dataclass
class PurchaseOrderItem:
    id: str
    purchase_order_id: str
    description: str
    quantity: int
    unit_cost_cents: int
    total_cost_cents: int
    asset_type: Optional[str] = None
    received_quantity: int = 0
    received_at: Optional[datetime] = None
    linked_asset_id: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class PurchaseOrder:
    id: str
    company_id: str
    po_number: str
    vendor_name: str
    department_id: str
    status: PurchaseOrderStatus
    total_amount_cents: int
    currency: str
    created_by: str
    vendor_id: Optional[str] = None
    notes: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    ordered_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None
    items: list[PurchaseOrderItem] = field(default_factory=list)
    request_ids: list[str] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        company_id: str,
        po_number: str,
        vendor_name: str,
        department_id: str,
        created_by: str,
        currency: str = "USD",
        vendor_id: Optional[str] = None,
        notes: Optional[str] = None,
        id: Optional[str] = None,
    ) -> "PurchaseOrder":
        return cls(
            id=id or str(ulid.new()),
            company_id=company_id,
            po_number=po_number,
            vendor_name=vendor_name,
            department_id=department_id,
            status=PurchaseOrderStatus.DRAFT,
            total_amount_cents=0,
            currency=currency,
            created_by=created_by,
            vendor_id=vendor_id,
            notes=notes,
        )

    def _transition(self, target: PurchaseOrderStatus) -> None:
        allowed = VALID_TRANSITIONS.get(self.status, [])
        if target not in allowed:
            raise InvalidPOStatusTransitionError(
                self.status, target,
            )
        self.status = target

    def submit(self) -> None:
        if not self.items:
            raise ValueError(
                "Cannot submit a PO with no items"
            )
        if self.total_amount_cents <= 0:
            raise ValueError(
                "Cannot submit a PO with total <= 0"
            )
        self._transition(PurchaseOrderStatus.SUBMITTED)

    def approve(self, approved_by: str) -> None:
        self._transition(PurchaseOrderStatus.APPROVED)
        self.approved_by = approved_by
        self.approved_at = datetime.now(UTC)

    def reject(self, reason: str) -> None:
        self._transition(PurchaseOrderStatus.CANCELLED)
        self.cancellation_reason = reason

    def mark_ordered(self) -> None:
        self._transition(PurchaseOrderStatus.ORDERED)
        self.ordered_at = datetime.now(UTC)

    def cancel(self, reason: str) -> None:
        self._transition(PurchaseOrderStatus.CANCELLED)
        self.cancellation_reason = reason

    def receive(self) -> None:
        all_received = all(
            item.received_quantity >= item.quantity
            for item in self.items
        )
        if all_received:
            self._transition(PurchaseOrderStatus.RECEIVED)
        else:
            self._transition(
                PurchaseOrderStatus.PARTIALLY_RECEIVED,
            )

    def close(self) -> None:
        self._transition(PurchaseOrderStatus.CLOSED)

    def recalculate_total(self) -> None:
        self.total_amount_cents = sum(
            item.total_cost_cents for item in self.items
        )
