from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from src.framework.application.command_bus import (
    Command,
    CommandHandler,
)
from src.maintenance_bc.maintenance_record.domain.enums import (
    MaintenancePriority,
)
from src.maintenance_bc.maintenance_record.domain.repository import (
    MaintenanceRecordRepositoryInterface,
)


class MaintenanceRecordNotFoundError(Exception):
    pass


@dataclass
class UpdateMaintenanceRecordCommand(Command):
    record_id: str
    company_id: str
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    checklist_items: Optional[list[str]] = None
    scheduled_at: Optional[datetime] = None


class UpdateMaintenanceRecordCommandHandler(
    CommandHandler[UpdateMaintenanceRecordCommand],
):
    def __init__(
        self,
        record_repo: MaintenanceRecordRepositoryInterface,
    ):
        self.record_repo = record_repo

    def handle(
        self,
        command: UpdateMaintenanceRecordCommand,
    ) -> None:
        record = self.record_repo.find_by_id(
            command.record_id,
            command.company_id,
        )
        if not record:
            raise MaintenanceRecordNotFoundError("Maintenance record not found")

        record.update_scheduled(
            title=command.title,
            description=command.description,
            priority=(
                MaintenancePriority(command.priority)
                if command.priority is not None
                else None
            ),
            checklist_items=command.checklist_items,
            scheduled_at=command.scheduled_at,
        )

        self.record_repo.save(record)
