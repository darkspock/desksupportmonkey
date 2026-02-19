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
class StartMaintenanceCommand(Command):
    record_id: str
    company_id: str


class StartMaintenanceCommandHandler(
    CommandHandler[StartMaintenanceCommand],
):
    def __init__(
        self,
        record_repo: MaintenanceRecordRepositoryInterface,
    ):
        self.record_repo = record_repo

    def handle(
        self,
        command: StartMaintenanceCommand,
    ) -> None:
        record = self.record_repo.find_by_id(
            command.record_id,
            command.company_id,
        )
        if not record:
            raise MaintenanceRecordNotFoundError("Maintenance record not found")

        record.start()
        self.record_repo.save(record)
