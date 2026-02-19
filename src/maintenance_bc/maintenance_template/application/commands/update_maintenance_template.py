from dataclasses import dataclass
from typing import Optional

from src.framework.application.command_bus import (
    Command,
    CommandHandler,
)
from src.maintenance_bc.maintenance_record.domain.enums import (
    MaintenancePriority,
    RecurrenceFrequency,
)
from src.maintenance_bc.maintenance_template.domain.entities import (
    ChecklistItem,
)
from src.maintenance_bc.maintenance_template.domain.repository import (
    MaintenanceTemplateRepositoryInterface,
)


class MaintenanceTemplateNotFoundError(Exception):
    pass


@dataclass
class UpdateMaintenanceTemplateCommand(Command):
    template_id: str
    company_id: str
    name: Optional[str] = None
    default_priority: Optional[str] = None
    description: Optional[str] = None
    recurrence_frequency: Optional[str] = None
    recurrence_interval: Optional[int] = None
    asset_type_filter: Optional[str] = None
    checklist_items: list[dict] | None = None


class UpdateMaintenanceTemplateCommandHandler(
    CommandHandler[UpdateMaintenanceTemplateCommand],
):
    def __init__(
        self,
        template_repo: MaintenanceTemplateRepositoryInterface,
    ):
        self.template_repo = template_repo

    def handle(
        self,
        command: UpdateMaintenanceTemplateCommand,
    ) -> None:
        template = self.template_repo.find_by_id(
            command.template_id,
            command.company_id,
        )
        if not template:
            raise MaintenanceTemplateNotFoundError("Maintenance template not found")

        template.update(
            name=command.name,
            description=command.description,
            default_priority=(
                MaintenancePriority(command.default_priority)
                if command.default_priority
                else None
            ),
            recurrence_frequency=(
                RecurrenceFrequency(command.recurrence_frequency)
                if command.recurrence_frequency
                else None
            ),
            recurrence_interval=command.recurrence_interval,
            asset_type_filter=command.asset_type_filter,
            checklist_items=(
                [
                    ChecklistItem.create(
                        title=item.get("title", ""),
                        description=item.get("description"),
                        is_required=item.get("is_required", True),
                    )
                    for item in command.checklist_items
                ]
                if command.checklist_items is not None
                else None
            ),
        )
        self.template_repo.save(template)
