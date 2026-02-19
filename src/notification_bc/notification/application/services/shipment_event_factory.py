from src.notification_bc.notification.domain.enums import (
    EventType,
)
from src.notification_bc.notification.domain.events import (
    DomainEvent,
)
from src.shipping_bc.shipment.domain.entities import (
    Shipment,
)


class ShipmentEventFactory:

    @staticmethod
    def shipment_created(
        shipment: Shipment, actor_id: str,
    ) -> DomainEvent:
        return DomainEvent(
            event_type=EventType.SHIPMENT_CREATED,
            company_id=shipment.company_id,
            actor_id=actor_id,
            payload={
                "shipment_id": shipment.id,
                "direction": shipment.direction.value,
                "destination_type": (
                    shipment.destination_type.value
                ),
                "recipient_user_id": (
                    shipment.recipient_user_id
                ),
                "created_by": shipment.created_by,
                "item_count": len(shipment.items),
            },
            title="Shipment created",
            body=(
                f"{shipment.direction.value} shipment "
                f"with {len(shipment.items)} item(s)"
            ),
        )

    @staticmethod
    def shipment_dispatched(
        shipment: Shipment, actor_id: str,
    ) -> DomainEvent:
        return DomainEvent(
            event_type=EventType.SHIPMENT_DISPATCHED,
            company_id=shipment.company_id,
            actor_id=actor_id,
            payload={
                "shipment_id": shipment.id,
                "direction": shipment.direction.value,
                "recipient_user_id": (
                    shipment.recipient_user_id
                ),
                "created_by": shipment.created_by,
                "carrier": shipment.carrier,
                "tracking_number": (
                    shipment.tracking_number
                ),
            },
            title="Shipment dispatched",
            body=(
                f"Shipped via {shipment.carrier} — "
                f"tracking: {shipment.tracking_number}"
            ),
        )

    @staticmethod
    def shipment_delivered(
        shipment: Shipment, actor_id: str,
    ) -> DomainEvent:
        return DomainEvent(
            event_type=EventType.SHIPMENT_DELIVERED,
            company_id=shipment.company_id,
            actor_id=actor_id,
            payload={
                "shipment_id": shipment.id,
                "direction": shipment.direction.value,
                "recipient_user_id": (
                    shipment.recipient_user_id
                ),
                "created_by": shipment.created_by,
            },
            title="Shipment delivered",
            body="Your shipment has been delivered",
        )

    @staticmethod
    def shipment_failed(
        shipment: Shipment, actor_id: str,
    ) -> DomainEvent:
        return DomainEvent(
            event_type=EventType.SHIPMENT_FAILED,
            company_id=shipment.company_id,
            actor_id=actor_id,
            payload={
                "shipment_id": shipment.id,
                "direction": shipment.direction.value,
                "recipient_user_id": (
                    shipment.recipient_user_id
                ),
                "created_by": shipment.created_by,
                "failure_reason": (
                    shipment.failure_reason
                ),
            },
            title="Shipment failed",
            body=(
                f"Shipment failed: "
                f"{shipment.failure_reason or 'Unknown'}"
            ),
        )

    @staticmethod
    def shipment_cancelled(
        shipment: Shipment, actor_id: str,
    ) -> DomainEvent:
        return DomainEvent(
            event_type=EventType.SHIPMENT_CANCELLED,
            company_id=shipment.company_id,
            actor_id=actor_id,
            payload={
                "shipment_id": shipment.id,
                "direction": shipment.direction.value,
                "recipient_user_id": (
                    shipment.recipient_user_id
                ),
                "created_by": shipment.created_by,
                "cancellation_reason": (
                    shipment.cancellation_reason
                ),
            },
            title="Shipment cancelled",
            body=(
                f"Shipment cancelled: "
                f"{shipment.cancellation_reason or 'No reason'}"
            ),
        )
