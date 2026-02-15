from src.notification_bc.notification.domain.enums import EventType
from src.notification_bc.notification.domain.events import DomainEvent
from src.request_bc.request.domain.entities import ServiceRequest


class RequestEventFactory:

    @staticmethod
    def request_created(request: ServiceRequest, actor_id: str) -> DomainEvent:
        return DomainEvent(
            event_type=EventType.REQUEST_CREATED,
            company_id=request.company_id,
            actor_id=actor_id,
            payload={
                "request_id": request.id,
                "created_by": request.created_by,
                "assigned_to": request.assigned_to,
                "type": request.type.value,
                "title": request.title,
            },
            title=f"New {request.type.value.replace('_', ' ')} request",
            body=request.title,
        )

    @staticmethod
    def status_changed(
        request: ServiceRequest, old_status: str, new_status: str, actor_id: str,
    ) -> DomainEvent:
        return DomainEvent(
            event_type=EventType.REQUEST_STATUS_CHANGED,
            company_id=request.company_id,
            actor_id=actor_id,
            payload={
                "request_id": request.id,
                "created_by": request.created_by,
                "assigned_to": request.assigned_to,
                "old_status": old_status,
                "new_status": new_status,
            },
            title="Request updated",
            body=f"Status changed from {old_status} to {new_status}",
        )

    @staticmethod
    def priority_changed(
        request: ServiceRequest, old_priority: str, new_priority: str, actor_id: str,
    ) -> DomainEvent:
        return DomainEvent(
            event_type=EventType.REQUEST_PRIORITY_CHANGED,
            company_id=request.company_id,
            actor_id=actor_id,
            payload={
                "request_id": request.id,
                "created_by": request.created_by,
                "assigned_to": request.assigned_to,
                "old_priority": old_priority,
                "new_priority": new_priority,
            },
            title="Priority changed",
            body=f"Priority changed from {old_priority} to {new_priority}",
        )

    @staticmethod
    def request_assigned(request: ServiceRequest, actor_id: str) -> DomainEvent:
        return DomainEvent(
            event_type=EventType.REQUEST_ASSIGNED,
            company_id=request.company_id,
            actor_id=actor_id,
            payload={
                "request_id": request.id,
                "created_by": request.created_by,
                "assigned_to": request.assigned_to,
            },
            title="Request assigned",
            body=f"Assigned to {request.assigned_to}",
        )

    @staticmethod
    def comment_added(request: ServiceRequest, actor_id: str) -> DomainEvent:
        return DomainEvent(
            event_type=EventType.REQUEST_COMMENT_ADDED,
            company_id=request.company_id,
            actor_id=actor_id,
            payload={
                "request_id": request.id,
                "created_by": request.created_by,
                "assigned_to": request.assigned_to,
            },
            title="New comment",
            body=f"Comment on: {request.title}",
        )

    @staticmethod
    def note_added(request: ServiceRequest, actor_id: str) -> DomainEvent:
        return DomainEvent(
            event_type=EventType.REQUEST_NOTE_ADDED,
            company_id=request.company_id,
            actor_id=actor_id,
            payload={
                "request_id": request.id,
                "created_by": request.created_by,
                "assigned_to": request.assigned_to,
            },
            title="New internal note",
            body=f"Note on: {request.title}",
        )
