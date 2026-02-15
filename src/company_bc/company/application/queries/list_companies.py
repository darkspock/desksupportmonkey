from dataclasses import dataclass
from typing import Optional

from src.company_bc.company.domain.entities import Company
from src.company_bc.company.domain.repository import CompanyRepositoryInterface


@dataclass
class ListCompaniesQuery:
    page: int = 1
    page_size: int = 20
    search: Optional[str] = None


class ListCompaniesQueryHandler:
    def __init__(self, company_repo: CompanyRepositoryInterface):
        self.company_repo = company_repo

    def handle(self, query: ListCompaniesQuery) -> tuple[list[Company], int]:
        return self.company_repo.find_all(
            page=query.page,
            page_size=query.page_size,
            search=query.search,
        )
