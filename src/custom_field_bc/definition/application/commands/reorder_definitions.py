from dataclasses import dataclass

from src.framework.application.command_bus import Command, CommandHandler
from src.custom_field_bc.definition.domain.repository import (
    CustomFieldDefinitionRepositoryInterface,
)


@dataclass
class ReorderFieldDefinitionsCommand(Command):
    company_id: str
    entity_type: str
    field_ids: list[str]


class ReorderFieldDefinitionsCommandHandler(
    CommandHandler[ReorderFieldDefinitionsCommand]
):
    def __init__(self, repo: CustomFieldDefinitionRepositoryInterface):
        self.repo = repo

    def handle(self, command: ReorderFieldDefinitionsCommand) -> None:
        updates = [
            (field_id, index)
            for index, field_id in enumerate(command.field_ids)
        ]
        self.repo.bulk_update_sort_order(updates)
