from dataclasses import dataclass
from typing import Optional

from src.framework.application.command_bus import Command, CommandHandler
from src.custom_field_bc.definition.domain.entities import CustomFieldDefinition
from src.custom_field_bc.definition.domain.exceptions import (
    DuplicateFieldKeyError,
    MaxFieldsExceededError,
)
from src.custom_field_bc.definition.domain.repository import (
    CustomFieldDefinitionRepositoryInterface,
)


MAX_FIELDS_PER_ENTITY = 20


@dataclass
class CreateFieldDefinitionCommand(Command):
    definition_id: str
    company_id: str
    entity_type: str
    label: str
    field_type: str
    description: Optional[str] = None
    options: Optional[list[str]] = None
    required: bool = False
    sort_order: int = 0
    visible_to_employees: bool = True


class CreateFieldDefinitionCommandHandler(
    CommandHandler[CreateFieldDefinitionCommand]
):
    def __init__(self, repo: CustomFieldDefinitionRepositoryInterface):
        self.repo = repo

    def handle(self, command: CreateFieldDefinitionCommand) -> None:
        count = self.repo.count_by_entity_type(
            command.company_id, command.entity_type
        )
        if count >= MAX_FIELDS_PER_ENTITY:
            raise MaxFieldsExceededError(command.entity_type)

        definition = CustomFieldDefinition.create(
            company_id=command.company_id,
            entity_type=command.entity_type,
            label=command.label,
            field_type=command.field_type,
            description=command.description,
            options=command.options,
            required=command.required,
            sort_order=command.sort_order,
            visible_to_employees=command.visible_to_employees,
        )
        definition.id = command.definition_id

        if self.repo.has_field_key(
            command.company_id, command.entity_type, definition.field_key
        ):
            raise DuplicateFieldKeyError(definition.field_key, command.entity_type)

        self.repo.save(definition)
