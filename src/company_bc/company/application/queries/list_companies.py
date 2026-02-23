from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from src.company_bc.company.domain.billing_enums import BillingStatus, PlanTier
from src.company_bc.company.domain.enums import CompanyStatus
from src.company_bc.company.domain.repository import CompanyRepositoryInterface
from src.framework.application.query_bus import Query, QueryHandler


@dataclass
class CompanyListItemDto:
    id: str
    name: str
    status: CompanyStatus
    email_domains: list[str]
    is_active: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    plan: PlanTier
    billing_status: BillingStatus
    user_count: int
    asset_count: int
    trial_days_remaining: Optional[int]


@dataclass
class ListCompaniesQuery(Query):
    page: int = 1
    page_size: int = 20
    search: Optional[str] = None
    in_trial: Optional[bool] = None
    plan: Optional[str] = None


class ListCompaniesQueryHandler(QueryHandler[ListCompaniesQuery, tuple[list[CompanyListItemDto], int]]):
    def __init__(self, company_repo: CompanyRepositoryInterface):
        self.company_repo = company_repo

    def handle(self, query: ListCompaniesQuery) -> tuple[list[CompanyListItemDto], int]:
        rows, total = self.company_repo.find_all_with_counts(
            page=query.page,
            page_size=query.page_size,
            search=query.search,
            in_trial=query.in_trial,
            plan=query.plan,
        )
        now = datetime.now(timezone.utc)
        items: list[CompanyListItemDto] = []
        for company, user_count, asset_count in rows:
            trial_days_remaining: Optional[int] = None
            if company.is_in_trial() and company.trial_ends_at is not None:
                trial_end = company.trial_ends_at
                if trial_end.tzinfo is None:
                    trial_end = trial_end.replace(tzinfo=timezone.utc)
                trial_days_remaining = max(0, (trial_end - now).days)
            items.append(CompanyListItemDto(
                id=company.id,
                name=company.name,
                status=company.status,
                email_domains=company.email_domains,
                is_active=company.is_active,
                created_at=company.created_at,
                updated_at=company.updated_at,
                plan=company.plan,
                billing_status=company.billing_status,
                user_count=user_count,
                asset_count=asset_count,
                trial_days_remaining=trial_days_remaining,
            ))
        return items, total
