from dataclasses import dataclass

from src.framework.application.query_bus import (
    Query,
    QueryHandler,
)
from src.maintenance_bc.maintenance_record.domain.repository import (
    MaintenanceRecordRepositoryInterface,
)


@dataclass
class MaintenanceDashboardResult:
    scheduled: int
    overdue: int
    in_progress: int
    completed_30d: int


@dataclass
class MaintenanceDashboardQuery(Query):
    company_id: str


class MaintenanceDashboardQueryHandler(
    QueryHandler[
        MaintenanceDashboardQuery,
        MaintenanceDashboardResult,
    ],
):
    def __init__(
        self,
        record_repo: MaintenanceRecordRepositoryInterface,
    ):
        self.record_repo = record_repo

    def handle(
        self,
        query: MaintenanceDashboardQuery,
    ) -> MaintenanceDashboardResult:
        counts = self.record_repo.count_dashboard(
            query.company_id,
        )
        return MaintenanceDashboardResult(
            scheduled=counts.get("scheduled", 0),
            overdue=counts.get("overdue", 0),
            in_progress=counts.get("in_progress", 0),
            completed_30d=counts.get("completed_30d", 0),
        )
