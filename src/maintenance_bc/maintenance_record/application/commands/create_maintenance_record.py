from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from src.framework.application.command_bus import (
    Command,
    CommandHandler,
)
from src.maintenance_bc.maintenance_record.application.ports import (
    AssetLookup,
    UserLookup,
)
from src.maintenance_bc.maintenance_record.domain.entities import (
    MaintenanceRecord,
)
from src.maintenance_bc.maintenance_record.domain.enums import (
    MaintenancePriority,
)
from src.maintenance_bc.maintenance_record.domain.repository import (
    MaintenanceRecordRepositoryInterface,
)


class AssetNotFoundError(Exception):
    pass


class TechnicianNotFoundError(Exception):
    pass


@dataclass
class CreateMaintenanceRecordCommand(Command):
    record_id: str
    company_id: str
    asset_id: str
    title: str
    created_by: str
    priority: str = "MEDIUM"
    description: Optional[str] = None
    technician_id: Optional[str] = None
    template_id: Optional[str] = None
    plan_id: Optional[str] = None
    checklist_items: Optional[list[str]] = None
    scheduled_at: Optional[datetime] = None


class CreateMaintenanceRecordCommandHandler(
    CommandHandler[CreateMaintenanceRecordCommand],
):
    def __init__(
        self,
        record_repo: MaintenanceRecordRepositoryInterface,
        asset_lookup: AssetLookup,
        user_lookup: UserLookup,
    ):
        self.record_repo = record_repo
        self.asset_lookup = asset_lookup
        self.user_lookup = user_lookup

    def handle(
        self,
        command: CreateMaintenanceRecordCommand,
    ) -> None:
        if not self.asset_lookup.exists(
            command.asset_id,
            command.company_id,
        ):
            raise AssetNotFoundError("Asset not found")

        if command.technician_id:
            user = self.user_lookup.find_by_id_and_company(
                command.technician_id,
                command.company_id,
            )
            if not user:
                raise TechnicianNotFoundError(
                    f"Technician '{command.technician_id}' not found"
                )

        record = MaintenanceRecord.create(
            id=command.record_id,
            company_id=command.company_id,
            asset_id=command.asset_id,
            title=command.title,
            priority=MaintenancePriority(command.priority),
            description=command.description,
            technician_id=command.technician_id,
            template_id=command.template_id,
            plan_id=command.plan_id,
            checklist_items=command.checklist_items,
            scheduled_at=command.scheduled_at,
        )
        self.record_repo.save(record)
