from src.maintenance_bc.maintenance_record.domain.entities import (
    MaintenanceRecord,
)
from src.notification_bc.notification.domain.enums import (
    EventType,
)
from src.notification_bc.notification.domain.events import (
    DomainEvent,
)


class MaintenanceEventFactory:

    @staticmethod
    def maintenance_scheduled(
        record: MaintenanceRecord,
        actor_id: str,
    ) -> DomainEvent:
        return DomainEvent(
            event_type=EventType.MAINTENANCE_SCHEDULED,
            company_id=record.company_id,
            actor_id=actor_id,
            payload={
                "maintenance_id": record.id,
                "asset_id": record.asset_id,
                "technician_id": record.technician_id,
                "scheduled_at": (
                    record.scheduled_at.isoformat() if record.scheduled_at else None
                ),
                "created_by": actor_id,
            },
            title="Maintenance scheduled",
            body=record.title,
        )

    @staticmethod
    def maintenance_completed(
        record: MaintenanceRecord,
        actor_id: str,
    ) -> DomainEvent:
        return DomainEvent(
            event_type=EventType.MAINTENANCE_COMPLETED,
            company_id=record.company_id,
            actor_id=actor_id,
            payload={
                "maintenance_id": record.id,
                "asset_id": record.asset_id,
                "technician_id": record.technician_id,
                "created_by": actor_id,
            },
            title="Maintenance completed",
            body=record.title,
        )

    @staticmethod
    def maintenance_cancelled(
        record: MaintenanceRecord,
        actor_id: str,
    ) -> DomainEvent:
        return DomainEvent(
            event_type=EventType.MAINTENANCE_CANCELLED,
            company_id=record.company_id,
            actor_id=actor_id,
            payload={
                "maintenance_id": record.id,
                "asset_id": record.asset_id,
                "technician_id": record.technician_id,
                "created_by": actor_id,
                "reason": record.cancellation_reason,
            },
            title="Maintenance cancelled",
            body=record.cancellation_reason or record.title,
        )
