from dataclasses import dataclass
from typing import Optional

from src.company_bc.assignment_config.domain.entities import (
    CompanyAssignmentAIConfig,
)
from src.company_bc.assignment_config.domain.repository import (
    AssignmentConfigRepositoryInterface,
)
from src.framework.application.query_bus import (
    Query,
    QueryHandler,
)


@dataclass
class GetCompanyAIConfigQuery(Query):
    company_id: str


class GetCompanyAIConfigQueryHandler(
    QueryHandler[
        GetCompanyAIConfigQuery,
        Optional[CompanyAssignmentAIConfig],
    ],
):
    def __init__(
        self,
        config_repo: AssignmentConfigRepositoryInterface,
    ):
        self.config_repo = config_repo

    def handle(
        self, query: GetCompanyAIConfigQuery,
    ) -> Optional[CompanyAssignmentAIConfig]:
        return self.config_repo.find_by_company(
            query.company_id,
        )
