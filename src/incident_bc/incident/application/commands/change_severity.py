from dataclasses import dataclass
from typing import Any, Optional

from src.framework.application.command_bus import Command, CommandHandler
from src.incident_bc.incident.domain.entities import IncidentTimeline
from src.incident_bc.incident.domain.enums import (
    IncidentSeverity,
    TimelineEventType,
)
from src.incident_bc.incident.domain.exceptions import IncidentNotFoundError
from src.incident_bc.incident.domain.repository import IncidentRepositoryInterface


@dataclass
class ChangeIncidentSeverityCommand(Command):
    incident_id: str
    company_id: str
    new_severity: str
    actor_id: str


class ChangeIncidentSeverityCommandHandler(
    CommandHandler[ChangeIncidentSeverityCommand]
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

    def handle(self, command: ChangeIncidentSeverityCommand) -> None:
        incident = self.incident_repo.find_by_id(
            command.incident_id, command.company_id
        )
        if not incident:
            raise IncidentNotFoundError(command.incident_id)

        old_severity = incident.severity.value
        new_severity = IncidentSeverity(command.new_severity)

        incident.change_severity(new_severity)
        self.incident_repo.save(incident)

        timeline_entry = IncidentTimeline.create(
            incident_id=incident.id,
            event_type=TimelineEventType.SEVERITY_CHANGE,
            description=f"Severity changed from {old_severity} to {new_severity.value}",
            actor_id=command.actor_id,
            metadata={
                "old_severity": old_severity,
                "new_severity": new_severity.value,
            },
        )
        self.incident_repo.save_timeline(timeline_entry)

        if self.event_bus and self.db:
            from src.incident_bc.incident.application.services.incident_event_factory import (
                IncidentEventFactory,
            )

            event = IncidentEventFactory.severity_changed(
                incident, old_severity, new_severity.value, command.actor_id
            )
            self.event_bus.publish(event, self.db)
