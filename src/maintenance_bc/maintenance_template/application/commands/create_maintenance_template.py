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
    MaintenanceTemplate,
)
from src.maintenance_bc.maintenance_template.domain.repository import (
    MaintenanceTemplateRepositoryInterface,
)


@dataclass
class CreateMaintenanceTemplateCommand(Command):
    template_id: str
    company_id: str
    name: str
    default_priority: str = "MEDIUM"
    description: Optional[str] = None
    recurrence_frequency: Optional[str] = None
    recurrence_interval: int = 1
    asset_type_filter: Optional[str] = None
    checklist_items: list[dict] | None = None


class CreateMaintenanceTemplateCommandHandler(
    CommandHandler[CreateMaintenanceTemplateCommand],
):
    def __init__(
        self,
        template_repo: MaintenanceTemplateRepositoryInterface,
    ):
        self.template_repo = template_repo

    def handle(
        self,
        command: CreateMaintenanceTemplateCommand,
    ) -> None:
        template = MaintenanceTemplate.create(
            id=command.template_id,
            company_id=command.company_id,
            name=command.name,
            description=command.description,
            default_priority=MaintenancePriority(command.default_priority),
            recurrence_frequency=(
                RecurrenceFrequency(command.recurrence_frequency)
                if command.recurrence_frequency
                else None
            ),
            recurrence_interval=command.recurrence_interval,
            asset_type_filter=command.asset_type_filter,
            checklist_items=[
                ChecklistItem.create(
                    title=item.get("title", ""),
                    description=item.get("description"),
                    is_required=item.get("is_required", True),
                )
                for item in (command.checklist_items or [])
            ],
        )
        self.template_repo.save(template)
