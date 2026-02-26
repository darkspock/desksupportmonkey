from typing import Optional

from src.asset_bc.checkout.application.ports import MaintenanceRecordCreator
from src.maintenance_bc.maintenance_record.application.commands.create_maintenance_record import (
    CreateMaintenanceRecordCommand,
    CreateMaintenanceRecordCommandHandler,
)
from src.maintenance_bc.maintenance_record.domain.repository import (
    MaintenanceRecordRepositoryInterface,
)
from src.maintenance_bc.maintenance_record.application.ports import (
    AssetLookup,
    UserLookup,
)


class MaintenanceRecordCreatorAdapter(MaintenanceRecordCreator):
    """Adapter that satisfies the asset_bc port by delegating to maintenance_bc command."""

    def __init__(
        self,
        record_repo: MaintenanceRecordRepositoryInterface,
        asset_lookup: AssetLookup,
        user_lookup: UserLookup,
    ):
        self.handler = CreateMaintenanceRecordCommandHandler(
            record_repo=record_repo,
            asset_lookup=asset_lookup,
            user_lookup=user_lookup,
        )

    def create(
        self,
        record_id: str,
        company_id: str,
        asset_id: str,
        title: str,
        created_by: str,
        priority: str = "HIGH",
        description: Optional[str] = None,
        source_type: Optional[str] = None,
    ) -> None:
        self.handler.handle(
            CreateMaintenanceRecordCommand(
                record_id=record_id,
                company_id=company_id,
                asset_id=asset_id,
                title=title,
                created_by=created_by,
                priority=priority,
                description=description,
                source_type=source_type,
            )
        )
