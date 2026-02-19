from dataclasses import dataclass

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
class CancelMaintenanceCommand(Command):
    record_id: str
    company_id: str
    reason: str


class CancelMaintenanceCommandHandler(
    CommandHandler[CancelMaintenanceCommand],
):
    def __init__(
        self,
        record_repo: MaintenanceRecordRepositoryInterface,
    ):
        self.record_repo = record_repo

    def handle(
        self,
        command: CancelMaintenanceCommand,
    ) -> None:
        record = self.record_repo.find_by_id(
            command.record_id,
            command.company_id,
        )
        if not record:
            raise MaintenanceRecordNotFoundError("Maintenance record not found")

        record.cancel(command.reason)
        self.record_repo.save(record)
