from dataclasses import dataclass
from typing import Optional

from src.framework.application.command_bus import Command, CommandHandler
from src.incident_bc.incident.domain.entities import IncidentTimeline
from src.incident_bc.incident.domain.enums import TimelineEventType
from src.incident_bc.incident.domain.exceptions import IncidentNotFoundError
from src.incident_bc.incident.domain.repository import IncidentRepositoryInterface


@dataclass
class UpdateIncidentCommand(Command):
    incident_id: str
    company_id: str
    actor_id: str
    title: Optional[str] = None
    description: Optional[str] = None
    attack_vector: Optional[str] = None
    data_breach_scope: Optional[str] = None


class UpdateIncidentCommandHandler(CommandHandler[UpdateIncidentCommand]):
    def __init__(self, incident_repo: IncidentRepositoryInterface):
        self.incident_repo = incident_repo

    def handle(self, command: UpdateIncidentCommand) -> None:
        incident = self.incident_repo.find_by_id(
            command.incident_id, command.company_id
        )
        if not incident:
            raise IncidentNotFoundError(command.incident_id)

        incident.update_details(
            title=command.title,
            description=command.description,
            attack_vector=command.attack_vector,
            data_breach_scope=command.data_breach_scope,
        )

        self.incident_repo.save(incident)

        timeline_entry = IncidentTimeline.create(
            incident_id=incident.id,
            event_type=TimelineEventType.INCIDENT_UPDATED,
            description="Incident details updated",
            actor_id=command.actor_id,
        )
        self.incident_repo.save_timeline(timeline_entry)
