from dataclasses import dataclass
from typing import Optional

from src.framework.application.command_bus import (
    Command,
    CommandHandler,
)
from src.maintenance_bc.maintenance_record.domain.repository import (
    MaintenanceRecordRepositoryInterface,
)


class MaintenanceRecordNotFoundError(Exception):
    pass


@dataclass
class CompleteMaintenanceCommand(Command):
    record_id: str
    company_id: str
    completion_notes: Optional[str] = None
    actual_findings: Optional[str] = None


class CompleteMaintenanceCommandHandler(
    CommandHandler[CompleteMaintenanceCommand],
):
    def __init__(
        self,
        record_repo: MaintenanceRecordRepositoryInterface,
    ):
        self.record_repo = record_repo

    def handle(
        self,
        command: CompleteMaintenanceCommand,
    ) -> None:
        record = self.record_repo.find_by_id(
            command.record_id,
            command.company_id,
        )
        if not record:
            raise MaintenanceRecordNotFoundError("Maintenance record not found")

        record.complete(
            completion_notes=command.completion_notes,
            actual_findings=command.actual_findings,
        )
        self.record_repo.save(record)
