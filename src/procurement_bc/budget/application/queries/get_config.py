from dataclasses import dataclass

from src.procurement_bc.budget.domain.entities import (
    CompanyProcurementConfig,
)
from src.procurement_bc.budget.domain.repository import (
    CompanyProcurementConfigRepositoryInterface,
)
from src.framework.application.query_bus import (
    Query,
    QueryHandler,
)


@dataclass
class GetProcurementConfigQuery(Query):
    company_id: str


class GetProcurementConfigQueryHandler(
    QueryHandler[
        GetProcurementConfigQuery,
        CompanyProcurementConfig,
    ],
):
    def __init__(
        self,
        config_repo: CompanyProcurementConfigRepositoryInterface,
    ):
        self.config_repo = config_repo

    def handle(
        self, query: GetProcurementConfigQuery,
    ) -> CompanyProcurementConfig:
        config = self.config_repo.find_by_company_id(
            query.company_id,
        )
        if config:
            return config
        return CompanyProcurementConfig.defaults(
            query.company_id,
        )
