from dataclasses import dataclass

from src.framework.application.command_bus import Command, CommandHandler
from src.custom_field_bc.definition.domain.exceptions import (
    FieldDefinitionNotFoundError,
)
from src.custom_field_bc.definition.domain.repository import (
    CustomFieldDefinitionRepositoryInterface,
)


@dataclass
class DeactivateFieldDefinitionCommand(Command):
    definition_id: str
    company_id: str


class DeactivateFieldDefinitionCommandHandler(
    CommandHandler[DeactivateFieldDefinitionCommand]
):
    def __init__(self, repo: CustomFieldDefinitionRepositoryInterface):
        self.repo = repo

    def handle(self, command: DeactivateFieldDefinitionCommand) -> None:
        definition = self.repo.find_by_id(
            command.definition_id, command.company_id
        )
        if not definition:
            raise FieldDefinitionNotFoundError(command.definition_id)

        definition.deactivate()
        self.repo.save(definition)
