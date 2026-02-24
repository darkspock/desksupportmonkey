from dataclasses import dataclass
from typing import Any, Optional

from src.framework.application.command_bus import Command, CommandHandler
from src.incident_bc.incident.domain.entities import IncidentTimeline
from src.incident_bc.incident.domain.enums import (
    IncidentStatus,
    TimelineEventType,
)
from src.incident_bc.incident.domain.exceptions import IncidentNotFoundError
from src.incident_bc.incident.domain.repository import IncidentRepositoryInterface


@dataclass
class ChangeIncidentStatusCommand(Command):
    incident_id: str
    company_id: str
    new_status: str
    actor_id: str
    close_reason: Optional[str] = None


class ChangeIncidentStatusCommandHandler(
    CommandHandler[ChangeIncidentStatusCommand]
):
    def __init__(
        self,
        incident_repo: IncidentRepositoryInterface,
        event_bus: Optional[Any] = None,
        db: Optional[Any] = None,
    ):
        self.incident_repo = incident_repo
        self.event_bus = event_bus
        self.db = db

    def handle(self, command: ChangeIncidentStatusCommand) -> None:
        incident = self.incident_repo.find_by_id(
            command.incident_id, command.company_id
        )
        if not incident:
            raise IncidentNotFoundError(command.incident_id)

        old_status = incident.status.value
        new_status = IncidentStatus(command.new_status)

        incident.change_status(new_status, close_reason=command.close_reason)
        self.incident_repo.save(incident)

        timeline_entry = IncidentTimeline.create(
            incident_id=incident.id,
            event_type=TimelineEventType.STATUS_CHANGE,
            description=f"Status changed from {old_status} to {new_status.value}",
            actor_id=command.actor_id,
            metadata={
                "old_status": old_status,
                "new_status": new_status.value,
                "close_reason": command.close_reason,
            },
        )
        self.incident_repo.save_timeline(timeline_entry)

        if self.event_bus and self.db:
            from src.incident_bc.incident.application.services.incident_event_factory import (
                IncidentEventFactory,
            )

            event = IncidentEventFactory.status_changed(
                incident, old_status, new_status.value, command.actor_id
            )
            self.event_bus.publish(event, self.db)
