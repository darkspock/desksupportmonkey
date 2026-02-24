from dataclasses import dataclass
from typing import Optional

from sqlalchemy.exc import IntegrityError

from src.framework.application.command_bus import Command, CommandHandler
from src.incident_bc.incident.domain.entities import IncidentTimeline
from src.incident_bc.incident.domain.enums import TimelineEventType
from src.incident_bc.incident.domain.exceptions import (
    AssetAlreadyLinkedError,
    IncidentClosedError,
    IncidentNotFoundError,
)
from src.incident_bc.incident.domain.repository import IncidentRepositoryInterface


@dataclass
class LinkAssetCommand(Command):
    incident_id: str
    company_id: str
    asset_id: str
    actor_id: str
    impact_description: Optional[str] = None


class LinkAssetCommandHandler(CommandHandler[LinkAssetCommand]):
    def __init__(self, incident_repo: IncidentRepositoryInterface):
        self.incident_repo = incident_repo

    def handle(self, command: LinkAssetCommand) -> None:
        incident = self.incident_repo.find_by_id(
            command.incident_id, command.company_id
        )
        if not incident:
            raise IncidentNotFoundError(command.incident_id)

        from src.incident_bc.incident.domain.enums import IncidentStatus

        if incident.status == IncidentStatus.CLOSED:
            raise IncidentClosedError()

        try:
            self.incident_repo.save_incident_asset(
                incident_id=command.incident_id,
                asset_id=command.asset_id,
                impact_description=command.impact_description,
            )
        except IntegrityError:
            raise AssetAlreadyLinkedError(command.asset_id)

        timeline_entry = IncidentTimeline.create(
            incident_id=command.incident_id,
            event_type=TimelineEventType.ASSET_LINKED,
            description="Asset linked to incident",
            actor_id=command.actor_id,
            metadata={
                "asset_id": command.asset_id,
                "impact_description": command.impact_description,
            },
        )
        self.incident_repo.save_timeline(timeline_entry)
