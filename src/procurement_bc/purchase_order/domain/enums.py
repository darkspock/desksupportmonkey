from enum import Enum


class PurchaseOrderStatus(str, Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    ORDERED = "ORDERED"
    PARTIALLY_RECEIVED = "PARTIALLY_RECEIVED"
    RECEIVED = "RECEIVED"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"

    @property
    def is_terminal(self) -> bool:
        return self in (
            PurchaseOrderStatus.CLOSED,
            PurchaseOrderStatus.CANCELLED,
        )

    @property
    def is_countable_for_budget(self) -> bool:
        return self in (
            PurchaseOrderStatus.APPROVED,
            PurchaseOrderStatus.ORDERED,
            PurchaseOrderStatus.PARTIALLY_RECEIVED,
            PurchaseOrderStatus.RECEIVED,
            PurchaseOrderStatus.CLOSED,
        )


VALID_TRANSITIONS: dict[
    PurchaseOrderStatus, list[PurchaseOrderStatus]
] = {
    PurchaseOrderStatus.DRAFT: [
        PurchaseOrderStatus.SUBMITTED,
        PurchaseOrderStatus.CANCELLED,
    ],
    PurchaseOrderStatus.SUBMITTED: [
        PurchaseOrderStatus.APPROVED,
        PurchaseOrderStatus.CANCELLED,
    ],
    PurchaseOrderStatus.APPROVED: [
        PurchaseOrderStatus.ORDERED,
        PurchaseOrderStatus.CANCELLED,
    ],
    PurchaseOrderStatus.ORDERED: [
        PurchaseOrderStatus.PARTIALLY_RECEIVED,
        PurchaseOrderStatus.RECEIVED,
        PurchaseOrderStatus.CANCELLED,
    ],
    PurchaseOrderStatus.PARTIALLY_RECEIVED: [
        PurchaseOrderStatus.PARTIALLY_RECEIVED,
        PurchaseOrderStatus.RECEIVED,
        PurchaseOrderStatus.CLOSED,
    ],
    PurchaseOrderStatus.RECEIVED: [
        PurchaseOrderStatus.CLOSED,
    ],
    PurchaseOrderStatus.CLOSED: [],
    PurchaseOrderStatus.CANCELLED: [],
}


class InvalidPOStatusTransitionError(Exception):
    def __init__(
        self,
        current: PurchaseOrderStatus,
        target: PurchaseOrderStatus,
    ):
        self.current = current
        self.target = target
        super().__init__(
            f"Cannot transition from {current.value} to {target.value}"
        )
