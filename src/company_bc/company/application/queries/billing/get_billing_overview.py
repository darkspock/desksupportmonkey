from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from src.company_bc.company.domain.billing_enums import BillingStatus, PlanTier
from src.company_bc.company.domain.plan_gate import PlanGate
from src.company_bc.company.domain.repository import CompanyRepositoryInterface
from src.framework.application.query_bus import Query, QueryHandler


class CompanyNotFoundError(Exception):
    pass


@dataclass
class BillingOverviewDto:
    plan: PlanTier
    billing_status: BillingStatus
    complimentary: bool
    user_count: int
    user_limit: Optional[int]
    asset_count: int
    asset_limit: Optional[int]
    grace_days_remaining: Optional[int]
    current_period_end: Optional[datetime]
    pending_downgrade_plan: Optional[PlanTier]


@dataclass
class GetBillingOverviewQuery(Query):
    company_id: str


class GetBillingOverviewQueryHandler(QueryHandler[GetBillingOverviewQuery, BillingOverviewDto]):
    def __init__(self, company_repo: CompanyRepositoryInterface) -> None:
        self.company_repo = company_repo

    def handle(self, query: GetBillingOverviewQuery) -> BillingOverviewDto:
        company = self.company_repo.find_by_id(query.company_id)
        if not company:
            raise CompanyNotFoundError("Company not found")

        user_count = self.company_repo.count_users(query.company_id)
        asset_count = self.company_repo.count_assets(query.company_id)

        grace_days_remaining: Optional[int] = None
        if company.grace_period_started_at:
            started = company.grace_period_started_at
            if started.tzinfo is None:
                started = started.replace(tzinfo=timezone.utc)
            elapsed_days = (datetime.now(timezone.utc) - started).days
            grace_days_remaining = max(0, 15 - elapsed_days)

        return BillingOverviewDto(
            plan=company.plan,
            billing_status=company.billing_status,
            complimentary=company.complimentary,
            user_count=user_count,
            user_limit=PlanGate.get_user_limit(company.plan),
            asset_count=asset_count,
            asset_limit=PlanGate.get_asset_limit(company.plan),
            grace_days_remaining=grace_days_remaining,
            current_period_end=company.current_period_end,
            pending_downgrade_plan=company.pending_downgrade_plan,
        )
