from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from core.stripe_client import StripeClient
from src.company_bc.company.domain.billing_enums import PlanTier
from src.company_bc.company.domain.plan_gate import (
    MILESTONE_TARGETS_CENTS,
    PLAN_PRICE_CENTS,
)
from src.company_bc.company.domain.repository import CompanyRepositoryInterface
from src.framework.application.query_bus import Query, QueryHandler


@dataclass
class PlanMrrDto:
    plan: str
    count: int
    mrr_cents: int


@dataclass
class RevenueSectionDto:
    mrr_cents: int
    mrr_formatted: str
    new_mrr_cents: int
    churned_mrr_cents: int
    net_new_mrr_cents: int
    by_plan: list[PlanMrrDto]


@dataclass
class TrialPipelineDto:
    active: int
    expiring_7d: int
    expiring_30d: int
    started_this_month: int


@dataclass
class CompanyHealthDto:
    total_active: int
    grace_period: int
    suspended: int
    complimentary: int
    failed_payments: int


@dataclass
class GrowthDto:
    new_7d: int
    new_30d: int
    mom_growth_pct: Optional[float]


@dataclass
class MilestoneDto:
    label: str
    description: str
    target_cents: int
    current_cents: int
    pct: int
    achieved: bool


@dataclass
class UpcomingRenewalDto:
    company_id: str
    company_name: str
    plan: str
    period_end: datetime


@dataclass
class FounderDashboardDto:
    revenue: RevenueSectionDto
    trials: TrialPipelineDto
    health: CompanyHealthDto
    growth: GrowthDto
    next_milestone: MilestoneDto
    upcoming_renewals_7d: list[UpcomingRenewalDto]
    as_of: datetime


@dataclass
class GetFounderDashboardQuery(Query):
    pass


def _compute_next_milestone(mrr_cents: int) -> MilestoneDto:
    for m in MILESTONE_TARGETS_CENTS:
        target = int(m["amount_cents"])  # type: ignore[call-overload]
        if mrr_cents < target:
            pct = min(100, int(mrr_cents * 100 / target)) if target > 0 else 100
            return MilestoneDto(
                label=str(m["label"]),
                description=str(m["description"]),
                target_cents=target,
                current_cents=mrr_cents,
                pct=pct,
                achieved=False,
            )
    last = MILESTONE_TARGETS_CENTS[-1]
    return MilestoneDto(
        label=str(last["label"]),
        description=str(last["description"]),
        target_cents=int(last["amount_cents"]),  # type: ignore[call-overload]
        current_cents=mrr_cents,
        pct=100,
        achieved=True,
    )


class GetFounderDashboardQueryHandler(
    QueryHandler[GetFounderDashboardQuery, FounderDashboardDto]
):
    def __init__(
        self,
        company_repo: CompanyRepositoryInterface,
        stripe_client: StripeClient,
    ) -> None:
        self.company_repo = company_repo
        self.stripe_client = stripe_client

    def handle(self, query: GetFounderDashboardQuery) -> FounderDashboardDto:
        now = datetime.now(timezone.utc)
        stats = self.company_repo.get_dashboard_stats(now)

        mrr_cents = sum(
            stats["plan_counts"].get(plan, 0) * PLAN_PRICE_CENTS[plan]
            for plan in [PlanTier.STARTER, PlanTier.PREMIUM, PlanTier.ENTERPRISE]
        )

        failed_payments = 0
        for customer_id in stats.get("at_risk_stripe_ids", []):
            try:
                invoices = self.stripe_client.list_invoices(customer_id, limit=5)
                failed_payments += sum(
                    1 for inv in invoices
                    if inv.get("status") in ("open", "uncollectible")
                )
            except Exception:
                pass

        next_milestone = _compute_next_milestone(mrr_cents)

        new_mrr_cents = stats.get("new_paying_this_month", 0) * (
            PLAN_PRICE_CENTS[PlanTier.PREMIUM]
        )
        churned_mrr_cents = stats.get("churned_this_month_cents", 0)

        revenue = RevenueSectionDto(
            mrr_cents=mrr_cents,
            mrr_formatted=f"€{mrr_cents / 100:,.0f}",
            new_mrr_cents=new_mrr_cents,
            churned_mrr_cents=churned_mrr_cents,
            net_new_mrr_cents=new_mrr_cents - churned_mrr_cents,
            by_plan=[
                PlanMrrDto(
                    plan=p.value,
                    count=stats["plan_counts"].get(p, 0),
                    mrr_cents=stats["plan_counts"].get(p, 0) * PLAN_PRICE_CENTS[p],
                )
                for p in [PlanTier.STARTER, PlanTier.PREMIUM, PlanTier.ENTERPRISE]
            ],
        )

        return FounderDashboardDto(
            revenue=revenue,
            trials=TrialPipelineDto(
                active=stats.get("trials_active", 0),
                expiring_7d=stats.get("trials_expiring_7d", 0),
                expiring_30d=stats.get("trials_expiring_30d", 0),
                started_this_month=stats.get("trials_started_this_month", 0),
            ),
            health=CompanyHealthDto(
                total_active=stats.get("total_active", 0),
                grace_period=stats.get("grace_period_count", 0),
                suspended=stats.get("suspended_count", 0),
                complimentary=stats.get("complimentary_count", 0),
                failed_payments=failed_payments,
            ),
            growth=GrowthDto(
                new_7d=stats.get("new_7d", 0),
                new_30d=stats.get("new_30d", 0),
                mom_growth_pct=stats.get("mom_growth_pct"),
            ),
            next_milestone=next_milestone,
            upcoming_renewals_7d=stats.get("upcoming_renewals_7d", []),
            as_of=now,
        )
