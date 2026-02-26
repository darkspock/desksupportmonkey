from dataclasses import dataclass

from src.asset_bc.asset.application.ports import UserLookup
from src.asset_bc.asset.domain.entities import Asset, AssetEvent, InvalidAssignmentError
from src.asset_bc.asset.domain.repository import AssetRepositoryInterface
from src.framework.application.command_bus import Command, CommandHandler


class AssetNotFoundError(Exception):
    pass


class UserNotFoundError(Exception):
    pass


class UserInactiveError(Exception):
    pass


@dataclass
class AssignAssetCommand(Command):
    asset_id: str
    company_id: str
    user_id: str
    performed_by: str


class AssignAssetCommandHandler(CommandHandler[AssignAssetCommand]):
    def __init__(
        self,
        asset_repo: AssetRepositoryInterface,
        user_repo: UserLookup,
    ):
        self.asset_repo = asset_repo
        self.user_repo = user_repo

    def handle(self, command: AssignAssetCommand) -> None:
        asset = self.asset_repo.find_by_id(command.asset_id, command.company_id)
        if not asset:
            raise AssetNotFoundError(f"Asset '{command.asset_id}' not found")

        user = self.user_repo.find_by_id_and_company(command.user_id, command.company_id)
        if not user:
            raise UserNotFoundError(f"User '{command.user_id}' not found")

        if not user.is_active:
            raise UserInactiveError(f"User '{command.user_id}' is inactive")

        asset.assign(user_id=command.user_id, department_id=user.department_id)
        self.asset_repo.save(asset)

        event = AssetEvent.create(
            asset_id=asset.id,
            event_type="assigned",
            data={
                "user_id": command.user_id,
                "assigned_by": command.performed_by,
                "department_id": user.department_id,
            },
            performed_by=command.performed_by,
        )
        self.asset_repo.save_event(event)
