from dataclasses import dataclass
from typing import Optional

from src.asset_bc.asset.domain.entities import Asset, AssetEvent
from src.asset_bc.asset.domain.enums import AssetCriticality
from src.asset_bc.asset.domain.repository import AssetRepositoryInterface
from src.framework.application.command_bus import Command, CommandHandler


class AssetNotFoundError(Exception):
    pass


@dataclass
class SetCriticalityCommand(Command):
    asset_id: str
    company_id: str
    criticality: Optional[str]  # None to clear
    performed_by: str


class SetCriticalityCommandHandler(CommandHandler[SetCriticalityCommand]):
    def __init__(self, asset_repo: AssetRepositoryInterface):
        self.asset_repo = asset_repo

    def handle(self, command: SetCriticalityCommand) -> None:
        asset = self.asset_repo.find_by_id(command.asset_id, command.company_id)
        if not asset:
            raise AssetNotFoundError(f"Asset '{command.asset_id}' not found")

        criticality_enum = AssetCriticality(command.criticality) if command.criticality else None
        changes = asset.set_criticality(criticality_enum)

        self.asset_repo.save(asset)

        if changes:
            event = AssetEvent.create(
                asset_id=asset.id,
                event_type="criticality_set",
                data=changes,
                performed_by=command.performed_by,
            )
            self.asset_repo.save_event(event)
