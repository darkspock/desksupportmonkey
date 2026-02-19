from dataclasses import dataclass

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


class MaintenanceTemplateNotFoundError(Exception):
    pass


@dataclass
class GetMaintenanceTemplateQuery(Query):
    template_id: str
    company_id: str


class GetMaintenanceTemplateQueryHandler(
    QueryHandler[
        GetMaintenanceTemplateQuery,
        MaintenanceTemplate,
    ],
):
    def __init__(
        self,
        template_repo: MaintenanceTemplateRepositoryInterface,
    ):
        self.template_repo = template_repo

    def handle(
        self,
        query: GetMaintenanceTemplateQuery,
    ) -> MaintenanceTemplate:
        template = self.template_repo.find_by_id(
            query.template_id,
            query.company_id,
        )
        if not template:
            raise MaintenanceTemplateNotFoundError("Maintenance template not found")
        return template
