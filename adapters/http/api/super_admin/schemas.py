from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PlanMrrResponse(BaseModel):
    plan: str
    count: int
    mrr_cents: int


class RevenueResponse(BaseModel):
    mrr_cents: int
    mrr_formatted: str
    new_mrr_cents: int
    churned_mrr_cents: int
    net_new_mrr_cents: int
    by_plan: list[PlanMrrResponse]


class TrialPipelineResponse(BaseModel):
    active: int
    expiring_7d: int
    expiring_30d: int
    started_this_month: int


class CompanyHealthResponse(BaseModel):
    total_active: int
    grace_period: int
    suspended: int
    complimentary: int
    failed_payments: int


class GrowthResponse(BaseModel):
    new_7d: int
    new_30d: int
    mom_growth_pct: Optional[float] = None


class MilestoneResponse(BaseModel):
    label: str
    description: str
    target_cents: int
    current_cents: int
    pct: int
    achieved: bool


class UpcomingRenewalResponse(BaseModel):
    company_id: str
    company_name: str
    plan: str
    period_end: datetime


class FounderDashboardResponse(BaseModel):
    revenue: RevenueResponse
    trials: TrialPipelineResponse
    health: CompanyHealthResponse
    growth: GrowthResponse
    next_milestone: MilestoneResponse
    upcoming_renewals_7d: list[UpcomingRenewalResponse]
    as_of: datetime
