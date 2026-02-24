from dataclasses import dataclass

from src.framework.application.command_bus import Command, CommandHandler
from src.asset_bc.asset.domain.repository import AssetRepositoryInterface
from src.asset_type_bc.definition.domain.exceptions import (
    AssetTypeDefinitionNotFoundError,
    AssetTypeInUseError,
)
from src.asset_type_bc.definition.domain.repository import (
    AssetTypeDefinitionRepositoryInterface,
)


@dataclass
class DeleteAssetTypeCommand(Command):
    definition_id: str
    company_id: str


class DeleteAssetTypeCommandHandler(
    CommandHandler[DeleteAssetTypeCommand]
):
    def __init__(
        self,
        repo: AssetTypeDefinitionRepositoryInterface,
        asset_repo: AssetRepositoryInterface,
    ):
        self.repo = repo
        self.asset_repo = asset_repo

    def handle(self, command: DeleteAssetTypeCommand) -> None:
        definition = self.repo.find_by_id(
            command.definition_id, command.company_id
        )
        if not definition:
            raise AssetTypeDefinitionNotFoundError(
                command.definition_id
            )

        # Check if any assets use this type code
        assets, count = self.asset_repo.find_all(
            company_id=command.company_id,
            page=1,
            page_size=1,
            type=definition.code,
        )
        if count > 0:
            raise AssetTypeInUseError(definition.code)

        self.repo.delete(command.definition_id)
