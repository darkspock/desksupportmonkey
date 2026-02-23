from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from src.company_bc.company.domain.billing_enums import BillingStatus, PlanTier
from src.company_bc.company.domain.repository import CompanyRepositoryInterface
from src.framework.application.query_bus import Query, QueryHandler


class CompanyNotFoundError(Exception):
    pass


@dataclass
class CompanyBillingDto:
    company_id: str
    company_name: str
    plan: PlanTier
    billing_status: BillingStatus
    complimentary: bool
    stripe_customer_id: Optional[str]
    stripe_subscription_id: Optional[str]
    current_period_end: Optional[datetime]
    pending_downgrade_plan: Optional[PlanTier]
    grace_period_started_at: Optional[datetime]


@dataclass
class GetCompanyBillingQuery(Query):
    company_id: str


class GetCompanyBillingQueryHandler(QueryHandler[GetCompanyBillingQuery, CompanyBillingDto]):
    def __init__(self, company_repo: CompanyRepositoryInterface) -> None:
        self.company_repo = company_repo

    def handle(self, query: GetCompanyBillingQuery) -> CompanyBillingDto:
        company = self.company_repo.find_by_id(query.company_id)
        if not company:
            raise CompanyNotFoundError("Company not found")
        return CompanyBillingDto(
            company_id=company.id,
            company_name=company.name,
            plan=company.plan,
            billing_status=company.billing_status,
            complimentary=company.complimentary,
            stripe_customer_id=company.stripe_customer_id,
            stripe_subscription_id=company.stripe_subscription_id,
            current_period_end=company.current_period_end,
            pending_downgrade_plan=company.pending_downgrade_plan,
            grace_period_started_at=company.grace_period_started_at,
        )
