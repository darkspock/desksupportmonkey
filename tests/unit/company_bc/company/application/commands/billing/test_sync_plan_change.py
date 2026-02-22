from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from src.company_bc.company.application.commands.billing.sync_plan_change import (
    CompanyNotFoundError,
    SyncPlanChangeCommand,
    SyncPlanChangeCommandHandler,
)
from src.company_bc.company.domain.billing_enums import BillingStatus, PlanTier
from src.company_bc.company.domain.entities import Company


@pytest.fixture
def handler():
    return SyncPlanChangeCommandHandler(company_repo=MagicMock())


class TestSyncPlanChange:
    def test_updates_plan_and_period_end(self, handler):
        company = Company.create(name="Acme", email_domains=["acme.com"])
        handler.company_repo.find_by_stripe_customer_id.return_value = company
        period_end = datetime(2026, 5, 1, tzinfo=timezone.utc)

        handler.handle(
            SyncPlanChangeCommand(
                stripe_customer_id="cus_abc",
                new_plan=PlanTier.ENTERPRISE,
                subscription_status="active",
                current_period_end=period_end,
                pending_downgrade_plan=None,
            )
        )

        assert company.plan == PlanTier.ENTERPRISE
        assert company.current_period_end == period_end
        assert company.pending_downgrade_plan is None
        handler.company_repo.save.assert_called_once_with(company)

    def test_past_due_enters_grace_period(self, handler):
        company = Company.create(name="Acme", email_domains=["acme.com"])
        handler.company_repo.find_by_stripe_customer_id.return_value = company
        period_end = datetime(2026, 5, 1, tzinfo=timezone.utc)

        handler.handle(
            SyncPlanChangeCommand(
                stripe_customer_id="cus_abc",
                new_plan=PlanTier.PREMIUM,
                subscription_status="past_due",
                current_period_end=period_end,
                pending_downgrade_plan=None,
            )
        )

        assert company.billing_status == BillingStatus.GRACE_PERIOD
        assert company.grace_period_started_at is not None

    def test_company_not_found_raises(self, handler):
        handler.company_repo.find_by_stripe_customer_id.return_value = None

        with pytest.raises(CompanyNotFoundError):
            handler.handle(
                SyncPlanChangeCommand(
                    stripe_customer_id="cus_missing",
                    new_plan=PlanTier.PREMIUM,
                    subscription_status="active",
                    current_period_end=datetime(2026, 5, 1, tzinfo=timezone.utc),
                    pending_downgrade_plan=None,
                )
            )
