from dataclasses import dataclass

from src.framework.application.command_bus import Command, CommandHandler
from src.incident_bc.incident.domain.entities import IncidentTimeline
from src.incident_bc.incident.domain.enums import TimelineEventType
from src.incident_bc.incident.domain.exceptions import (
    IncidentClosedError,
    IncidentNotFoundError,
)
from src.incident_bc.incident.domain.repository import IncidentRepositoryInterface


@dataclass
class UnlinkAssetCommand(Command):
    incident_id: str
    company_id: str
    asset_id: str
    actor_id: str


class UnlinkAssetCommandHandler(CommandHandler[UnlinkAssetCommand]):
    def __init__(self, incident_repo: IncidentRepositoryInterface):
        self.incident_repo = incident_repo

    def handle(self, command: UnlinkAssetCommand) -> None:
        incident = self.incident_repo.find_by_id(
            command.incident_id, command.company_id
        )
        if not incident:
            raise IncidentNotFoundError(command.incident_id)

        from src.incident_bc.incident.domain.enums import IncidentStatus

        if incident.status == IncidentStatus.CLOSED:
            raise IncidentClosedError()

        self.incident_repo.delete_incident_asset(
            incident_id=command.incident_id,
            asset_id=command.asset_id,
        )

        timeline_entry = IncidentTimeline.create(
            incident_id=command.incident_id,
            event_type=TimelineEventType.ASSET_UNLINKED,
            description="Asset unlinked from incident",
            actor_id=command.actor_id,
            metadata={"asset_id": command.asset_id},
        )
        self.incident_repo.save_timeline(timeline_entry)
