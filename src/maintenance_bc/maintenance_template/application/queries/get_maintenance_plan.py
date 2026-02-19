from dataclasses import dataclass

from src.framework.application.query_bus import (
    Query,
    QueryHandler,
)
from src.maintenance_bc.maintenance_template.domain.entities import (
    MaintenancePlan,
)
from src.maintenance_bc.maintenance_template.domain.repository import (
    MaintenancePlanRepositoryInterface,
)


class MaintenancePlanNotFoundError(Exception):
    pass


@dataclass
class GetMaintenancePlanQuery(Query):
    plan_id: str
    company_id: str


class GetMaintenancePlanQueryHandler(
    QueryHandler[
        GetMaintenancePlanQuery,
        MaintenancePlan,
    ],
):
    def __init__(
        self,
        plan_repo: MaintenancePlanRepositoryInterface,
    ):
        self.plan_repo = plan_repo

    def handle(
        self,
        query: GetMaintenancePlanQuery,
    ) -> MaintenancePlan:
        plan = self.plan_repo.find_by_id(
            query.plan_id,
            query.company_id,
        )
        if not plan:
            raise MaintenancePlanNotFoundError("Maintenance plan not found")
        return plan
