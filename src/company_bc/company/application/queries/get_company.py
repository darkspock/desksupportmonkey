from dataclasses import dataclass

from src.company_bc.company.domain.entities import Company
from src.company_bc.company.domain.repository import CompanyRepositoryInterface
from src.framework.application.query_bus import Query, QueryHandler


class CompanyNotFoundError(Exception):
    pass


@dataclass
class GetCompanyQuery(Query):
    company_id: str


@dataclass
class CompanyDetail:
    company: Company
    user_count: int
    department_count: int


class GetCompanyQueryHandler(QueryHandler[GetCompanyQuery, CompanyDetail]):
    def __init__(self, company_repo: CompanyRepositoryInterface):
        self.company_repo = company_repo

    def handle(self, query: GetCompanyQuery) -> CompanyDetail:
        company = self.company_repo.find_by_id(query.company_id)
        if not company:
            raise CompanyNotFoundError("Company not found")

        user_count = self.company_repo.count_users(query.company_id)
        department_count = self.company_repo.count_departments(query.company_id)

        return CompanyDetail(
            company=company,
            user_count=user_count,
            department_count=department_count,
        )
