from dataclasses import dataclass

from src.framework.application.command_bus import (
    Command,
    CommandHandler,
)
from src.maintenance_bc.maintenance_record.application.ports import (
    UserLookup,
)
from src.maintenance_bc.maintenance_record.domain.repository import (
    MaintenanceRecordRepositoryInterface,
)


class MaintenanceRecordNotFoundError(Exception):
    pass


class TechnicianNotFoundError(Exception):
    pass


@dataclass
class AssignMaintenanceRecordCommand(Command):
    record_id: str
    company_id: str
    technician_id: str


class AssignMaintenanceRecordCommandHandler(
    CommandHandler[AssignMaintenanceRecordCommand],
):
    def __init__(
        self,
        record_repo: MaintenanceRecordRepositoryInterface,
        user_lookup: UserLookup,
    ):
        self.record_repo = record_repo
        self.user_lookup = user_lookup

    def handle(
        self,
        command: AssignMaintenanceRecordCommand,
    ) -> None:
        record = self.record_repo.find_by_id(
            command.record_id,
            command.company_id,
        )
        if not record:
            raise MaintenanceRecordNotFoundError("Maintenance record not found")

        user = self.user_lookup.find_by_id_and_company(
            command.technician_id,
            command.company_id,
        )
        if not user:
            raise TechnicianNotFoundError(
                f"Technician '{command.technician_id}' not found"
            )

        record.assign(command.technician_id)
        self.record_repo.save(record)
