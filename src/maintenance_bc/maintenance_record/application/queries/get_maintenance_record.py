from dataclasses import dataclass

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


class MaintenanceRecordNotFoundError(Exception):
    pass


@dataclass
class GetMaintenanceRecordQuery(Query):
    record_id: str
    company_id: str


class GetMaintenanceRecordQueryHandler(
    QueryHandler[
        GetMaintenanceRecordQuery,
        MaintenanceRecord,
    ],
):
    def __init__(
        self,
        record_repo: MaintenanceRecordRepositoryInterface,
    ):
        self.record_repo = record_repo

    def handle(
        self,
        query: GetMaintenanceRecordQuery,
    ) -> MaintenanceRecord:
        record = self.record_repo.find_by_id(
            query.record_id,
            query.company_id,
        )
        if not record:
            raise MaintenanceRecordNotFoundError("Maintenance record not found")
        return record
