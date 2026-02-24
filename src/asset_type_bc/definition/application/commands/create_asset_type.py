from dataclasses import dataclass
from typing import Optional

from src.framework.application.command_bus import Command, CommandHandler
from src.asset_type_bc.definition.domain.entities import AssetTypeDefinition
from src.asset_type_bc.definition.domain.exceptions import (
    DuplicateAssetTypeCodeError,
)
from src.asset_type_bc.definition.domain.repository import (
    AssetTypeDefinitionRepositoryInterface,
)


@dataclass
class CreateAssetTypeCommand(Command):
    definition_id: str
    company_id: str
    name: str
    icon: Optional[str] = None
    sort_order: int = 0


class CreateAssetTypeCommandHandler(
    CommandHandler[CreateAssetTypeCommand]
):
    def __init__(
        self, repo: AssetTypeDefinitionRepositoryInterface
    ):
        self.repo = repo

    def handle(self, command: CreateAssetTypeCommand) -> None:
        definition = AssetTypeDefinition.create(
            company_id=command.company_id,
            name=command.name,
            icon=command.icon,
            sort_order=command.sort_order,
        )
        definition.id = command.definition_id

        if self.repo.has_code(command.company_id, definition.code):
            raise DuplicateAssetTypeCodeError(definition.code)

        self.repo.save(definition)
