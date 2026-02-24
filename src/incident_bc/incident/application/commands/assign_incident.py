from dataclasses import dataclass
from typing import Any, Optional

from src.framework.application.command_bus import Command, CommandHandler
from src.incident_bc.incident.domain.entities import IncidentTimeline
from src.incident_bc.incident.domain.enums import TimelineEventType
from src.incident_bc.incident.domain.exceptions import IncidentNotFoundError
from src.incident_bc.incident.domain.repository import IncidentRepositoryInterface


@dataclass
class AssignIncidentCommand(Command):
    incident_id: str
    company_id: str
    assigned_to: str
    actor_id: str


class AssignIncidentCommandHandler(CommandHandler[AssignIncidentCommand]):
    def __init__(
        self,
        incident_repo: IncidentRepositoryInterface,
        event_bus: Optional[Any] = None,
        db: Optional[Any] = None,
    ):
        self.incident_repo = incident_repo
        self.event_bus = event_bus
        self.db = db

    def handle(self, command: AssignIncidentCommand) -> None:
        incident = self.incident_repo.find_by_id(
            command.incident_id, command.company_id
        )
        if not incident:
            raise IncidentNotFoundError(command.incident_id)

        incident.assign_to(command.assigned_to)
        self.incident_repo.save(incident)

        timeline_entry = IncidentTimeline.create(
            incident_id=incident.id,
            event_type=TimelineEventType.ASSIGNMENT,
            description=f"Incident assigned",
            actor_id=command.actor_id,
            metadata={"assigned_to": command.assigned_to},
        )
        self.incident_repo.save_timeline(timeline_entry)

        if self.event_bus and self.db:
            from src.incident_bc.incident.application.services.incident_event_factory import (
                IncidentEventFactory,
            )

            event = IncidentEventFactory.incident_assigned(
                incident, command.assigned_to, command.actor_id
            )
            self.event_bus.publish(event, self.db)
