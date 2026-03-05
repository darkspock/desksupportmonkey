"""Query to list all active company memberships for a user."""

from dataclasses import dataclass

from src.auth_bc.company_user.domain.repository import CompanyUserRepositoryInterface
from src.auth_bc.user.domain.repository import UserRepositoryInterface
from src.company_bc.company.domain.repository import CompanyRepositoryInterface
from src.framework.application.query_bus import Query, QueryHandler


@dataclass
class UserCompanyDto:
    company_id: str
    company_name: str
    slug: str
    role: str
    is_current: bool


@dataclass
class ListUserCompaniesQuery(Query):
    user_id: str


class ListUserCompaniesQueryHandler(
    QueryHandler[ListUserCompaniesQuery, list[UserCompanyDto]]
):
    def __init__(
        self,
        company_user_repo: CompanyUserRepositoryInterface,
        company_repo: CompanyRepositoryInterface,
        user_repo: UserRepositoryInterface,
    ):
        self.company_user_repo = company_user_repo
        self.company_repo = company_repo
        self.user_repo = user_repo

    def handle(self, query: ListUserCompaniesQuery) -> list[UserCompanyDto]:
        # 1. Get user to know current company_id
        user = self.user_repo.find_by_id(query.user_id)
        if user is None:
            return []

        # 2. Get all active memberships
        memberships = self.company_user_repo.find_active_by_user_id(query.user_id)
        if not memberships:
            return []

        # 3. Batch-fetch companies (no N+1)
        company_ids = [m.company_id for m in memberships]
        companies = self.company_repo.find_by_ids(company_ids)
        company_map = {c.id: c for c in companies}

        # 4. Build DTOs
        result = []
        for m in memberships:
            company = company_map.get(m.company_id)
            if company is None or not company.is_active:
                continue
            result.append(UserCompanyDto(
                company_id=m.company_id,
                company_name=company.name,
                slug=company.slug or "",
                role=m.role.value,
                is_current=(m.company_id == user.company_id),
            ))
        return result
