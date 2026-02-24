from dataclasses import dataclass
from typing import Optional

from src.framework.application.command_bus import Command, CommandHandler
from src.custom_field_bc.definition.domain.exceptions import (
    FieldDefinitionNotFoundError,
)
from src.custom_field_bc.definition.domain.repository import (
    CustomFieldDefinitionRepositoryInterface,
)


@dataclass
class UpdateFieldDefinitionCommand(Command):
    definition_id: str
    company_id: str
    label: Optional[str] = None
    description: Optional[str] = None
    options: Optional[list[str]] = None
    required: Optional[bool] = None
    visible_to_employees: Optional[bool] = None


class UpdateFieldDefinitionCommandHandler(
    CommandHandler[UpdateFieldDefinitionCommand]
):
    def __init__(self, repo: CustomFieldDefinitionRepositoryInterface):
        self.repo = repo

    def handle(self, command: UpdateFieldDefinitionCommand) -> None:
        definition = self.repo.find_by_id(
            command.definition_id, command.company_id
        )
        if not definition:
            raise FieldDefinitionNotFoundError(command.definition_id)

        definition.update(
            label=command.label,
            description=command.description,
            required=command.required,
            options=command.options,
            visible_to_employees=command.visible_to_employees,
        )
        self.repo.save(definition)
