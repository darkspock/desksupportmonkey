from datetime import datetime, timezone
from unittest.mock import MagicMock

from src.company_bc.company.application.queries.get_founder_dashboard import (
    GetFounderDashboardQuery,
    GetFounderDashboardQueryHandler,
    UpcomingRenewalDto,
    _compute_next_milestone,
)
from src.company_bc.company.domain.billing_enums import PlanTier


def _make_handler(stats=None, stripe_invoices=None):
    repo = MagicMock()
    repo.get_dashboard_stats.return_value = stats or _default_stats()
    stripe = MagicMock()
    stripe.list_invoices.return_value = stripe_invoices or []
    return GetFounderDashboardQueryHandler(company_repo=repo, stripe_client=stripe)


def _default_stats():
    return {
        "total_active": 10,
        "plan_counts": {PlanTier.PREMIUM: 3, PlanTier.ENTERPRISE: 1},
        "grace_period_count": 1,
        "suspended_count": 0,
        "complimentary_count": 2,
        "trials_active": 5,
        "trials_expiring_7d": 2,
        "trials_expiring_30d": 4,
        "trials_started_this_month": 3,
        "new_7d": 2,
        "new_30d": 5,
        "new_paying_this_month": 1,
        "churned_this_month_cents": 0,
        "mom_growth_pct": 25.0,
        "upcoming_renewals_7d": [
            UpcomingRenewalDto(
                company_id="c1",
                company_name="Acme",
                plan="premium",
                period_end=datetime(2026, 3, 1, tzinfo=timezone.utc),
            )
        ],
        "at_risk_stripe_ids": [],
    }


class TestGetFounderDashboardQueryHandler:
    def test_mrr_calculated_correctly(self):
        handler = _make_handler()
        dto = handler.handle(GetFounderDashboardQuery())
        # 3 premium * 9900 + 1 enterprise * 19900 = 49600
        assert dto.revenue.mrr_cents == 49600

    def test_mrr_formatted(self):
        handler = _make_handler()
        dto = handler.handle(GetFounderDashboardQuery())
        assert dto.revenue.mrr_formatted == "€496"

    def test_trial_pipeline_populated(self):
        handler = _make_handler()
        dto = handler.handle(GetFounderDashboardQuery())
        assert dto.trials.active == 5
        assert dto.trials.expiring_7d == 2
        assert dto.trials.expiring_30d == 4
        assert dto.trials.started_this_month == 3

    def test_health_populated(self):
        handler = _make_handler()
        dto = handler.handle(GetFounderDashboardQuery())
        assert dto.health.total_active == 10
        assert dto.health.grace_period == 1
        assert dto.health.complimentary == 2

    def test_growth_populated(self):
        handler = _make_handler()
        dto = handler.handle(GetFounderDashboardQuery())
        assert dto.growth.new_7d == 2
        assert dto.growth.new_30d == 5
        assert dto.growth.mom_growth_pct == 25.0

    def test_upcoming_renewals(self):
        handler = _make_handler()
        dto = handler.handle(GetFounderDashboardQuery())
        assert len(dto.upcoming_renewals_7d) == 1
        assert dto.upcoming_renewals_7d[0].company_name == "Acme"

    def test_failed_payments_from_stripe(self):
        stats = _default_stats()
        stats["at_risk_stripe_ids"] = ["cus_risk1"]
        open_inv = [{"status": "open"}, {"status": "paid"}]
        handler = _make_handler(stats=stats, stripe_invoices=open_inv)
        dto = handler.handle(GetFounderDashboardQuery())
        assert dto.health.failed_payments == 1

    def test_zero_companies_returns_zeros(self):
        empty = {
            "total_active": 0,
            "plan_counts": {PlanTier.PREMIUM: 0, PlanTier.ENTERPRISE: 0},
            "grace_period_count": 0,
            "suspended_count": 0,
            "complimentary_count": 0,
            "trials_active": 0,
            "trials_expiring_7d": 0,
            "trials_expiring_30d": 0,
            "trials_started_this_month": 0,
            "new_7d": 0,
            "new_30d": 0,
            "new_paying_this_month": 0,
            "churned_this_month_cents": 0,
            "mom_growth_pct": None,
            "upcoming_renewals_7d": [],
            "at_risk_stripe_ids": [],
        }
        handler = _make_handler(stats=empty)
        dto = handler.handle(GetFounderDashboardQuery())
        assert dto.revenue.mrr_cents == 0
        assert dto.health.total_active == 0

    def test_as_of_is_set(self):
        handler = _make_handler()
        dto = handler.handle(GetFounderDashboardQuery())
        assert dto.as_of is not None


class TestComputeNextMilestone:
    def test_first_milestone_when_mrr_zero(self):
        m = _compute_next_milestone(0)
        assert m.label == "costs_covered"
        assert m.pct == 0
        assert m.achieved is False

    def test_between_milestones(self):
        m = _compute_next_milestone(26000)
        assert m.label == "founder_salary"
        assert m.achieved is False

    def test_all_milestones_achieved(self):
        m = _compute_next_milestone(800000)
        assert m.label == "head_of_growth"
        assert m.achieved is True
        assert m.pct == 100

    def test_pct_capped_at_100(self):
        m = _compute_next_milestone(25900)
        assert m.label == "founder_salary"
        assert m.pct <= 100
