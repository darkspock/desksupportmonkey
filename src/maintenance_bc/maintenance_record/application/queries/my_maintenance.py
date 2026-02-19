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


@dataclass
class MyMaintenanceQuery(Query):
    company_id: str
    technician_id: str
    page: int = 1
    page_size: int = 20


class MyMaintenanceQueryHandler(
    QueryHandler[
        MyMaintenanceQuery,
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
        query: MyMaintenanceQuery,
    ) -> tuple[list[MaintenanceRecord], int]:
        return self.record_repo.find_my_queue(
            company_id=query.company_id,
            technician_id=query.technician_id,
            page=query.page,
            page_size=query.page_size,
        )
