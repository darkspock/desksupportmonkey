from dataclasses import dataclass

from src.asset_bc.asset.domain.repository import AssetRepositoryInterface
from src.change_bc.change_request.domain.entities import (
    ChangeAsset,
    ChangeEvent,
)
from src.change_bc.change_request.domain.enums import (
    ChangeEventType,
    InvalidStatusTransitionError,
)
from src.change_bc.change_request.domain.exceptions import (
    ChangeNotFoundError,
)
from src.change_bc.change_request.domain.repository import (
    ChangeRequestRepositoryInterface,
)
from src.framework.application.command_bus import Command, CommandHandler


@dataclass
class LinkAssetsCommand(Command):
    change_id: str
    company_id: str
    asset_ids: list[str]
    actor_id: str


class LinkAssetsCommandHandler(CommandHandler[LinkAssetsCommand]):
    def __init__(
        self,
        change_repo: ChangeRequestRepositoryInterface,
        asset_repo: AssetRepositoryInterface,
    ):
        self.change_repo = change_repo
        self.asset_repo = asset_repo

    def handle(self, command: LinkAssetsCommand) -> None:
        change = self.change_repo.find_by_id(
            command.change_id, command.company_id
        )
        if not change:
            raise ChangeNotFoundError(command.change_id)
        if change.status.is_terminal:
            raise InvalidStatusTransitionError(
                change.status, change.status
            )

        existing = self.change_repo.find_assets_by_change(command.change_id)
        existing_ids = {ca.asset_id for ca in existing}

        linked = 0
        for asset_id in command.asset_ids:
            if asset_id in existing_ids:
                continue
            asset = self.asset_repo.find_by_id(
                asset_id, command.company_id
            )
            if not asset:
                continue
            ca = ChangeAsset.create(
                change_request_id=command.change_id,
                asset_id=asset_id,
            )
            self.change_repo.save_change_asset(ca)
            linked += 1

        if linked > 0:
            event = ChangeEvent.create(
                change_request_id=command.change_id,
                event_type=ChangeEventType.ASSET_LINKED,
                description=f"{linked} asset(s) linked",
                actor_id=command.actor_id,
                metadata={
                    "asset_ids": command.asset_ids,
                    "linked": linked,
                },
            )
            self.change_repo.save_event(event)
