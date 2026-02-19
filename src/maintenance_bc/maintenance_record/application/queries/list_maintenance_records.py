from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from src.framework.application.query_bus import (
    Query,
    QueryHandler,
)
from src.maintenance_bc.maintenance_record.domain.entities import (
    MaintenanceRecord,
)
from src.maintenance_bc.maintenance_record.domain.repository import (
    MaintenanceRecordRepositoryInterface,
)


@dataclass
class ListMaintenanceRecordsQuery(Query):
    company_id: str
    page: int = 1
    page_size: int = 20
    status: Optional[str] = None
    asset_id: Optional[str] = None
    technician_id: Optional[str] = None
    priority: Optional[str] = None
    scheduled_from: Optional[datetime] = None
    scheduled_to: Optional[datetime] = None


class ListMaintenanceRecordsQueryHandler(
    QueryHandler[
        ListMaintenanceRecordsQuery,
        tuple[list[MaintenanceRecord], int],
    ],
):
    def __init__(
        self,
        record_repo: MaintenanceRecordRepositoryInterface,
    ):
        self.record_repo = record_repo

    def handle(
        self,
        query: ListMaintenanceRecordsQuery,
    ) -> tuple[list[MaintenanceRecord], int]:
        return self.record_repo.find_all(
            company_id=query.company_id,
            page=query.page,
            page_size=query.page_size,
            status=query.status,
            asset_id=query.asset_id,
            technician_id=query.technician_id,
            priority=query.priority,
            scheduled_from=query.scheduled_from,
            scheduled_to=query.scheduled_to,
        )
