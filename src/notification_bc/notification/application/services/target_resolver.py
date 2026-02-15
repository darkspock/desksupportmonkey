from src.auth_bc.user.domain.repository import UserRepositoryInterface
from src.notification_bc.notification.domain.enums import EventType
from src.notification_bc.notification.domain.events import DomainEvent


class TargetResolver:
    def __init__(self, user_repo: UserRepositoryInterface):
        self.user_repo = user_repo

    def resolve(self, event: DomainEvent) -> list[str]:
        resolvers = {
            EventType.REQUEST_CREATED: self._resolve_request_created,
            EventType.REQUEST_STATUS_CHANGED: self._resolve_request_status_changed,
            EventType.REQUEST_ASSIGNED: self._resolve_request_assigned,
            EventType.REQUEST_PRIORITY_CHANGED: self._resolve_request_priority_changed,
            EventType.REQUEST_COMMENT_ADDED: self._resolve_request_comment_added,
            EventType.REQUEST_NOTE_ADDED: self._resolve_request_note_added,
            EventType.REPORT_READY: self._resolve_report_ready,
        }
        resolver = resolvers.get(event.event_type)
        if resolver is None:
            return []
        targets = resolver(event)
        targets.discard(event.actor_id)
        return list(targets)

    def _resolve_request_created(self, event: DomainEvent) -> set[str]:
        tech_ids = self.user_repo.find_technician_ids_by_company(event.company_id)
        return set(tech_ids)

    def _resolve_request_status_changed(self, event: DomainEvent) -> set[str]:
        targets = set()
        created_by = event.payload.get("created_by")
        assigned_to = event.payload.get("assigned_to")
        if created_by:
            targets.add(created_by)
        if assigned_to:
            targets.add(assigned_to)
        return targets

    def _resolve_request_assigned(self, event: DomainEvent) -> set[str]:
        targets = set()
        assigned_to = event.payload.get("assigned_to")
        if assigned_to:
            targets.add(assigned_to)
        return targets

    def _resolve_request_priority_changed(self, event: DomainEvent) -> set[str]:
        targets = set()
        assigned_to = event.payload.get("assigned_to")
        if assigned_to:
            targets.add(assigned_to)
        return targets

    def _resolve_request_comment_added(self, event: DomainEvent) -> set[str]:
        targets = set()
        created_by = event.payload.get("created_by")
        assigned_to = event.payload.get("assigned_to")
        if created_by:
            targets.add(created_by)
        if assigned_to:
            targets.add(assigned_to)
        return targets

    def _resolve_request_note_added(self, event: DomainEvent) -> set[str]:
        targets = set()
        assigned_to = event.payload.get("assigned_to")
        if assigned_to:
            targets.add(assigned_to)
        return targets

    def _resolve_report_ready(self, event: DomainEvent) -> set[str]:
        requested_by = event.payload.get("requested_by")
        return {requested_by} if requested_by else set()
