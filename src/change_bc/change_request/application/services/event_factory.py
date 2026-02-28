from src.change_bc.change_request.domain.entities import ChangeRequest
from src.notification_bc.notification.domain.enums import EventType
from src.notification_bc.notification.domain.events import DomainEvent


class ChangeEventFactory:

    @staticmethod
    def change_approved(
        change: ChangeRequest, actor_id: str,
    ) -> DomainEvent:
        return DomainEvent(
            event_type=EventType.CHANGE_APPROVED,
            company_id=change.company_id,
            actor_id=actor_id,
            payload={
                "change_id": change.id,
                "title": change.title,
                "change_type": change.change_type.value,
                "requested_by": change.requested_by,
            },
            title="Change request approved",
            body=change.title,
        )

    @staticmethod
    def change_rejected(
        change: ChangeRequest, actor_id: str, reason: str,
    ) -> DomainEvent:
        return DomainEvent(
            event_type=EventType.CHANGE_REJECTED,
            company_id=change.company_id,
            actor_id=actor_id,
            payload={
                "change_id": change.id,
                "title": change.title,
                "change_type": change.change_type.value,
                "reason": reason,
                "requested_by": change.requested_by,
            },
            title="Change request rejected",
            body=f"{change.title}: {reason}",
        )
