from dataclasses import dataclass

from src.change_bc.change_request.domain.entities import ChangeEvent
from src.change_bc.change_request.domain.enums import (
    ChangeEventType,
    ChangeStatus,
)
from src.change_bc.change_request.domain.exceptions import (
    ChangeNotFoundError,
    ChangeNotUnlinkableError,
)
from src.change_bc.change_request.domain.repository import (
    ChangeRequestRepositoryInterface,
)
from src.framework.application.command_bus import Command, CommandHandler


@dataclass
class UnlinkAssetCommand(Command):
    change_id: str
    company_id: str
    asset_id: str
    actor_id: str


class UnlinkAssetCommandHandler(CommandHandler[UnlinkAssetCommand]):
    def __init__(
        self,
        change_repo: ChangeRequestRepositoryInterface,
    ):
        self.change_repo = change_repo

    def handle(self, command: UnlinkAssetCommand) -> None:
        change = self.change_repo.find_by_id(
            command.change_id, command.company_id
        )
        if not change:
            raise ChangeNotFoundError(command.change_id)

        allowed = {
            ChangeStatus.DRAFT,
            ChangeStatus.PENDING_APPROVAL,
            ChangeStatus.SCHEDULED,
        }
        if change.status not in allowed:
            raise ChangeNotUnlinkableError(change.status.value)

        self.change_repo.delete_change_asset(
            command.change_id, command.asset_id
        )

        event = ChangeEvent.create(
            change_request_id=command.change_id,
            event_type=ChangeEventType.ASSET_UNLINKED,
            description="Asset unlinked",
            actor_id=command.actor_id,
            metadata={"asset_id": command.asset_id},
        )
        self.change_repo.save_event(event)
