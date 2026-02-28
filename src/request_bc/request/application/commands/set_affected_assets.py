from dataclasses import dataclass

from src.asset_bc.asset.domain.repository import AssetRepositoryInterface
from src.framework.application.command_bus import Command, CommandHandler
from src.request_bc.request.domain.entities import RequestEvent
from src.request_bc.request.domain.repository import RequestRepositoryInterface


class RequestNotFoundError(Exception):
    def __init__(self, request_id: str):
        super().__init__(f"Request not found: {request_id}")


class AssetNotFoundError(Exception):
    def __init__(self, missing_ids: list[str]):
        super().__init__(
            f"Assets not found: {', '.join(missing_ids)}"
        )


@dataclass
class SetAffectedAssetsCommand(Command):
    request_id: str
    company_id: str
    asset_ids: list[str]
    performed_by: str


class SetAffectedAssetsCommandHandler(
    CommandHandler[SetAffectedAssetsCommand],
):
    def __init__(
        self,
        request_repo: RequestRepositoryInterface,
        asset_repo: AssetRepositoryInterface,
    ):
        self.request_repo = request_repo
        self.asset_repo = asset_repo

    def handle(self, command: SetAffectedAssetsCommand) -> None:
        request = self.request_repo.find_by_id(
            command.request_id, command.company_id,
        )
        if not request:
            raise RequestNotFoundError(command.request_id)

        # Validate all asset IDs exist in company
        if command.asset_ids:
            found = self.asset_repo.find_by_ids(
                command.asset_ids, command.company_id,
            )
            found_ids = {a.id for a in found}
            missing = [
                aid for aid in command.asset_ids
                if aid not in found_ids
            ]
            if missing:
                raise AssetNotFoundError(missing)

        # Track old values for event
        old_ids = []
        if request.data:
            old_ids = request.data.get("affected_asset_ids", [])

        # Merge into existing data dict
        if request.data is None:
            request.data = {}
        request.data["affected_asset_ids"] = command.asset_ids

        self.request_repo.save(request)

        # Record event
        event = RequestEvent.create(
            request_id=command.request_id,
            event_type="affected_assets_updated",
            data={
                "old_asset_ids": old_ids,
                "new_asset_ids": command.asset_ids,
            },
            performed_by=command.performed_by,
        )
        self.request_repo.save_event(event)
