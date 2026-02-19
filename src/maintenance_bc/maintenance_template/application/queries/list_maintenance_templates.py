from dataclasses import dataclass
from typing import Optional

from src.framework.application.query_bus import (
    Query,
    QueryHandler,
)
from src.maintenance_bc.maintenance_template.domain.entities import (
    MaintenanceTemplate,
)
from src.maintenance_bc.maintenance_template.domain.repository import (
    MaintenanceTemplateRepositoryInterface,
)


@dataclass
class ListMaintenanceTemplatesQuery(Query):
    company_id: str
    page: int = 1
    page_size: int = 20
    is_active: Optional[bool] = True


class ListMaintenanceTemplatesQueryHandler(
    QueryHandler[
        ListMaintenanceTemplatesQuery,
        tuple[list[MaintenanceTemplate], int],
    ],
):
    def __init__(
        self,
        template_repo: MaintenanceTemplateRepositoryInterface,
    ):
        self.template_repo = template_repo

    def handle(
        self,
        query: ListMaintenanceTemplatesQuery,
    ) -> tuple[list[MaintenanceTemplate], int]:
        return self.template_repo.find_all(
            company_id=query.company_id,
            page=query.page,
            page_size=query.page_size,
            is_active=query.is_active,
        )
