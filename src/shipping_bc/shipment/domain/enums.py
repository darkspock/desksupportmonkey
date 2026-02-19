from enum import Enum


class ShipmentStatus(str, Enum):
    DRAFT = "DRAFT"
    DISPATCHED = "DISPATCHED"
    IN_TRANSIT = "IN_TRANSIT"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

    @property
    def is_terminal(self) -> bool:
        return self in (
            ShipmentStatus.DELIVERED,
            ShipmentStatus.FAILED,
            ShipmentStatus.CANCELLED,
        )

    @property
    def is_active(self) -> bool:
        return self in (
            ShipmentStatus.DRAFT,
            ShipmentStatus.DISPATCHED,
            ShipmentStatus.IN_TRANSIT,
        )


VALID_TRANSITIONS: dict[
    ShipmentStatus, list[ShipmentStatus]
] = {
    ShipmentStatus.DRAFT: [
        ShipmentStatus.DISPATCHED,
        ShipmentStatus.CANCELLED,
    ],
    ShipmentStatus.DISPATCHED: [
        ShipmentStatus.IN_TRANSIT,
        ShipmentStatus.DELIVERED,
        ShipmentStatus.FAILED,
        ShipmentStatus.CANCELLED,
    ],
    ShipmentStatus.IN_TRANSIT: [
        ShipmentStatus.DELIVERED,
        ShipmentStatus.FAILED,
        ShipmentStatus.CANCELLED,
    ],
    ShipmentStatus.DELIVERED: [],
    ShipmentStatus.FAILED: [],
    ShipmentStatus.CANCELLED: [],
}


class InvalidShipmentStatusTransitionError(Exception):
    def __init__(
        self,
        current: ShipmentStatus,
        target: ShipmentStatus,
    ):
        self.current = current
        self.target = target
        super().__init__(
            f"Cannot transition from {current.value} to {target.value}"
        )


class ShipmentDirection(str, Enum):
    OUTBOUND = "OUTBOUND"
    INBOUND = "INBOUND"


class DestinationType(str, Enum):
    EMPLOYEE_HOME = "EMPLOYEE_HOME"
    OFFICE = "OFFICE"
    VENDOR = "VENDOR"
