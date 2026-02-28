from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from src.company_bc.company.domain.repository import CompanyRepositoryInterface
from src.framework.application.query_bus import Query, QueryHandler


class CompanyNotFoundError(Exception):
    pass


@dataclass
class OnboardingStatusDto:
    sector: Optional[str]
    onboarding_completed_at: Optional[datetime]
    needs_onboarding: bool


@dataclass
class GetOnboardingStatusQuery(Query):
    company_id: str


class GetOnboardingStatusQueryHandler(QueryHandler[GetOnboardingStatusQuery, OnboardingStatusDto]):
    def __init__(self, company_repo: CompanyRepositoryInterface):
        self.company_repo = company_repo

    def handle(self, query: GetOnboardingStatusQuery) -> OnboardingStatusDto:
        company = self.company_repo.find_by_id(query.company_id)
        if not company:
            raise CompanyNotFoundError("Company not found")
        return OnboardingStatusDto(
            sector=company.sector,
            onboarding_completed_at=company.onboarding_completed_at,
            needs_onboarding=company.onboarding_completed_at is None,
        )
