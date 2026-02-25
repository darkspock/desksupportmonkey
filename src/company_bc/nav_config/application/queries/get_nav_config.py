from dataclasses import dataclass
from typing import Optional

from src.company_bc.nav_config.domain.entities import CompanyNavConfig
from src.company_bc.nav_config.domain.repository import (
    NavConfigRepositoryInterface,
)
from src.framework.application.query_bus import (
    Query,
    QueryHandler,
)


@dataclass
class GetNavConfigQuery(Query):
    company_id: str


class GetNavConfigQueryHandler(
    QueryHandler[
        GetNavConfigQuery,
        Optional[CompanyNavConfig],
    ],
):
    def __init__(
        self,
        nav_config_repo: NavConfigRepositoryInterface,
    ):
        self.nav_config_repo = nav_config_repo

    def handle(
        self, query: GetNavConfigQuery,
    ) -> Optional[CompanyNavConfig]:
        return self.nav_config_repo.find_by_company(
            query.company_id,
        )
