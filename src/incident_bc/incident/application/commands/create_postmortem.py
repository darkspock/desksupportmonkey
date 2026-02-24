from dataclasses import dataclass
from typing import Optional

from src.framework.application.command_bus import Command, CommandHandler
from src.incident_bc.incident.domain.entities import IncidentTimeline, PostMortem
from src.incident_bc.incident.domain.enums import IncidentStatus, TimelineEventType
from src.incident_bc.incident.domain.exceptions import (
    IncidentNotClosableForPostMortemError,
    IncidentNotFoundError,
    PostMortemAlreadyExistsError,
)
from src.incident_bc.incident.domain.repository import IncidentRepositoryInterface


@dataclass
class CreatePostMortemCommand(Command):
    incident_id: str
    company_id: str
    root_cause: str
    lessons_learned: str
    corrective_actions: str
    actor_id: str


class CreatePostMortemCommandHandler(CommandHandler[CreatePostMortemCommand]):
    def __init__(self, incident_repo: IncidentRepositoryInterface):
        self.incident_repo = incident_repo

    def handle(self, command: CreatePostMortemCommand) -> None:
        incident = self.incident_repo.find_by_id(
            command.incident_id, command.company_id
        )
        if not incident:
            raise IncidentNotFoundError(command.incident_id)

        if incident.status not in (
            IncidentStatus.RECOVERED,
            IncidentStatus.CLOSED,
        ):
            raise IncidentNotClosableForPostMortemError(incident.status.value)

        existing = self.incident_repo.find_postmortem_by_incident(
            command.incident_id
        )
        if existing:
            raise PostMortemAlreadyExistsError(command.incident_id)

        postmortem = PostMortem.create(
            incident_id=command.incident_id,
            root_cause=command.root_cause,
            lessons_learned=command.lessons_learned,
            corrective_actions=command.corrective_actions,
            created_by=command.actor_id,
        )

        self.incident_repo.save_postmortem(
            {
                "id": postmortem.id,
                "incident_id": postmortem.incident_id,
                "root_cause": postmortem.root_cause,
                "lessons_learned": postmortem.lessons_learned,
                "corrective_actions": postmortem.corrective_actions,
                "created_by": postmortem.created_by,
            }
        )

        timeline_entry = IncidentTimeline.create(
            incident_id=command.incident_id,
            event_type=TimelineEventType.POSTMORTEM_CREATED,
            description="Post-mortem created",
            actor_id=command.actor_id,
        )
        self.incident_repo.save_timeline(timeline_entry)
