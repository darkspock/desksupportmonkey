from dataclasses import dataclass
from typing import Optional

from src.asset_bc.asset.domain.entities import Asset, AssetEvent
from src.asset_bc.asset.domain.repository import AssetRepositoryInterface
from src.framework.application.command_bus import Command, CommandHandler


class AssetNotFoundError(Exception):
    pass


@dataclass
class UpdateBiaCommand(Command):
    asset_id: str
    company_id: str
    performed_by: str
    impact_score: Optional[int] = None
    rto_minutes: Optional[int] = None
    rpo_minutes: Optional[int] = None
    bia_justification: Optional[str] = None


class UpdateBiaCommandHandler(CommandHandler[UpdateBiaCommand]):
    def __init__(self, asset_repo: AssetRepositoryInterface):
        self.asset_repo = asset_repo

    def handle(self, command: UpdateBiaCommand) -> None:
        asset = self.asset_repo.find_by_id(command.asset_id, command.company_id)
        if not asset:
            raise AssetNotFoundError(f"Asset '{command.asset_id}' not found")

        changes = asset.update_bia(
            impact_score=command.impact_score,
            rto_minutes=command.rto_minutes,
            rpo_minutes=command.rpo_minutes,
            justification=command.bia_justification,
            reviewed_by=command.performed_by,
        )

        self.asset_repo.save(asset)

        if changes:
            event = AssetEvent.create(
                asset_id=asset.id,
                event_type="bia_updated",
                data=changes,
                performed_by=command.performed_by,
            )
            self.asset_repo.save_event(event)
