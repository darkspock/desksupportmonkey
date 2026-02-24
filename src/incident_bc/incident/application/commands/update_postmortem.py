from dataclasses import dataclass
from typing import Optional

from src.framework.application.command_bus import Command, CommandHandler
from src.incident_bc.incident.domain.entities import IncidentTimeline
from src.incident_bc.incident.domain.enums import TimelineEventType
from src.incident_bc.incident.domain.exceptions import (
    IncidentNotFoundError,
    PostMortemNotFoundError,
)
from src.incident_bc.incident.domain.repository import IncidentRepositoryInterface


@dataclass
class UpdatePostMortemCommand(Command):
    incident_id: str
    company_id: str
    actor_id: str
    root_cause: Optional[str] = None
    lessons_learned: Optional[str] = None
    corrective_actions: Optional[str] = None


class UpdatePostMortemCommandHandler(CommandHandler[UpdatePostMortemCommand]):
    def __init__(self, incident_repo: IncidentRepositoryInterface):
        self.incident_repo = incident_repo

    def handle(self, command: UpdatePostMortemCommand) -> None:
        incident = self.incident_repo.find_by_id(
            command.incident_id, command.company_id
        )
        if not incident:
            raise IncidentNotFoundError(command.incident_id)

        existing = self.incident_repo.find_postmortem_by_incident(
            command.incident_id
        )
        if not existing:
            raise PostMortemNotFoundError(command.incident_id)

        update_data: dict = {"incident_id": command.incident_id}
        if command.root_cause is not None:
            update_data["root_cause"] = command.root_cause.strip()
        if command.lessons_learned is not None:
            update_data["lessons_learned"] = command.lessons_learned.strip()
        if command.corrective_actions is not None:
            update_data["corrective_actions"] = command.corrective_actions.strip()

        self.incident_repo.save_postmortem(update_data)

        timeline_entry = IncidentTimeline.create(
            incident_id=command.incident_id,
            event_type=TimelineEventType.POSTMORTEM_UPDATED,
            description="Post-mortem updated",
            actor_id=command.actor_id,
        )
        self.incident_repo.save_timeline(timeline_entry)
