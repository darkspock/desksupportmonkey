from dataclasses import dataclass
from typing import Optional

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


@dataclass
class ListMaintenancePlansQuery(Query):
    company_id: str
    page: int = 1
    page_size: int = 20
    is_active: Optional[bool] = True
    template_id: Optional[str] = None
    asset_id: Optional[str] = None


class ListMaintenancePlansQueryHandler(
    QueryHandler[
        ListMaintenancePlansQuery,
        tuple[list[MaintenancePlan], int],
    ],
):
    def __init__(
        self,
        plan_repo: MaintenancePlanRepositoryInterface,
    ):
        self.plan_repo = plan_repo

    def handle(
        self,
        query: ListMaintenancePlansQuery,
    ) -> tuple[list[MaintenancePlan], int]:
        return self.plan_repo.find_all(
            company_id=query.company_id,
            page=query.page,
            page_size=query.page_size,
            is_active=query.is_active,
            template_id=query.template_id,
            asset_id=query.asset_id,
        )
