from datetime import datetime, timezone

import pytest

from src.company_bc.company.domain.billing_enums import BillingStatus, PlanTier
from src.company_bc.company.domain.entities import Company
from src.company_bc.company.domain.enums import CompanyStatus


def _company() -> Company:
    return Company.create(name="Acme Corp", email_domains=["acme.com"])


class TestEnterGracePeriod:
    def test_sets_billing_status(self):
        company = _company()
        company.enter_grace_period()
        assert company.billing_status == BillingStatus.GRACE_PERIOD

    def test_records_started_at(self):
        company = _company()
        before = datetime.now(timezone.utc)
        company.enter_grace_period()
        assert company.grace_period_started_at is not None
        assert company.grace_period_started_at >= before


class TestRestoreBilling:
    def test_clears_grace_period(self):
        company = _company()
        company.enter_grace_period()
        company.restore_billing()
        assert company.billing_status == BillingStatus.ACTIVE
        assert company.grace_period_started_at is None


class TestApplyPlanChange:
    def test_sets_plan_and_subscription(self):
        company = _company()
        period_end = datetime(2026, 4, 1, tzinfo=timezone.utc)
        company.apply_plan_change(PlanTier.PREMIUM, "sub_abc123", period_end)
        assert company.plan == PlanTier.PREMIUM
        assert company.stripe_subscription_id == "sub_abc123"
        assert company.current_period_end == period_end
        assert company.billing_status == BillingStatus.ACTIVE
        assert company.grace_period_started_at is None
        assert company.pending_downgrade_plan is None

    def test_clears_grace_period_on_plan_change(self):
        company = _company()
        company.enter_grace_period()
        period_end = datetime(2026, 4, 1, tzinfo=timezone.utc)
        company.apply_plan_change(PlanTier.ENTERPRISE, "sub_xyz", period_end)
        assert company.grace_period_started_at is None


class TestGrantComplimentary:
    def test_sets_complimentary_and_plan(self):
        company = _company()
        company.grant_complimentary(PlanTier.ENTERPRISE)
        assert company.complimentary is True
        assert company.plan == PlanTier.ENTERPRISE
        assert company.billing_status == BillingStatus.ACTIVE
        assert company.stripe_subscription_id is None

    def test_clears_existing_subscription(self):
        company = _company()
        company.stripe_subscription_id = "sub_old"
        company.grant_complimentary(PlanTier.PREMIUM)
        assert company.stripe_subscription_id is None


class TestRevokeComplimentary:
    def test_drops_to_free_over_limit(self):
        company = _company()
        company.grant_complimentary(PlanTier.ENTERPRISE)
        company.revoke_complimentary()
        assert company.complimentary is False
        assert company.plan == PlanTier.FREE
        assert company.billing_status == BillingStatus.OVER_LIMIT


class TestDefaultBillingFields:
    def test_new_company_has_free_plan(self):
        company = _company()
        assert company.plan == PlanTier.FREE
        assert company.billing_status == BillingStatus.ACTIVE
        assert company.complimentary is False
        assert company.stripe_customer_id is None
        assert company.stripe_subscription_id is None
