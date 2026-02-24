from dataclasses import dataclass

from src.framework.application.command_bus import Command, CommandHandler
from src.asset_type_bc.definition.domain.repository import (
    AssetTypeDefinitionRepositoryInterface,
)


@dataclass
class ReorderAssetTypesCommand(Command):
    company_id: str
    type_ids: list[str]


class ReorderAssetTypesCommandHandler(
    CommandHandler[ReorderAssetTypesCommand]
):
    def __init__(
        self, repo: AssetTypeDefinitionRepositoryInterface
    ):
        self.repo = repo

    def handle(self, command: ReorderAssetTypesCommand) -> None:
        updates = [
            (type_id, idx)
            for idx, type_id in enumerate(command.type_ids)
        ]
        self.repo.bulk_update_sort_order(updates)
