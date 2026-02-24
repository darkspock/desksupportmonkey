from dataclasses import dataclass, field
from typing import Optional

from src.framework.application.command_bus import Command, CommandHandler
from src.asset_type_bc.definition.domain.entities import _UNSET, _UnsetType
from src.asset_type_bc.definition.domain.exceptions import (
    AssetTypeDefinitionNotFoundError,
    DuplicateAssetTypeCodeError,
)
from src.asset_type_bc.definition.domain.repository import (
    AssetTypeDefinitionRepositoryInterface,
)


_SENTINEL = object()


@dataclass
class UpdateAssetTypeCommand(Command):
    definition_id: str
    company_id: str
    name: Optional[str] = None
    icon: object = field(default=_SENTINEL)
    is_active: Optional[bool] = None


class UpdateAssetTypeCommandHandler(
    CommandHandler[UpdateAssetTypeCommand]
):
    def __init__(
        self, repo: AssetTypeDefinitionRepositoryInterface
    ):
        self.repo = repo

    def handle(self, command: UpdateAssetTypeCommand) -> None:
        definition = self.repo.find_by_id(
            command.definition_id, command.company_id
        )
        if not definition:
            raise AssetTypeDefinitionNotFoundError(
                command.definition_id
            )

        icon_value: Optional[str] | _UnsetType = (
            _UNSET if command.icon is _SENTINEL else command.icon  # type: ignore[assignment]
        )

        definition.update(
            name=command.name,
            icon=icon_value,
            is_active=command.is_active,
        )

        # Check for duplicate code if name changed
        if command.name is not None:
            existing = self.repo.find_by_code(
                definition.code, command.company_id
            )
            if existing and existing.id != definition.id:
                raise DuplicateAssetTypeCodeError(definition.code)

        self.repo.save(definition)
