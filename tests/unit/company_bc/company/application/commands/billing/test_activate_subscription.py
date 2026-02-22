from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from src.company_bc.company.application.commands.billing.activate_subscription import (
    ActivateSubscriptionCommand,
    ActivateSubscriptionCommandHandler,
    CompanyNotFoundError,
)
from src.company_bc.company.domain.billing_enums import BillingStatus, PlanTier
from src.company_bc.company.domain.entities import Company


@pytest.fixture
def handler():
    return ActivateSubscriptionCommandHandler(company_repo=MagicMock())


class TestActivateSubscription:
    def test_activates_plan_and_subscription(self, handler):
        company = Company.create(name="Acme", email_domains=["acme.com"])
        company.stripe_customer_id = "cus_abc"
        handler.company_repo.find_by_stripe_customer_id.return_value = company
        period_end = datetime(2026, 4, 1, tzinfo=timezone.utc)

        handler.handle(
            ActivateSubscriptionCommand(
                stripe_customer_id="cus_abc",
                stripe_subscription_id="sub_123",
                plan=PlanTier.PREMIUM,
                current_period_end=period_end,
            )
        )

        assert company.plan == PlanTier.PREMIUM
        assert company.stripe_subscription_id == "sub_123"
        assert company.current_period_end == period_end
        assert company.billing_status == BillingStatus.ACTIVE
        handler.company_repo.save.assert_called_once_with(company)

    def test_company_not_found_raises(self, handler):
        handler.company_repo.find_by_stripe_customer_id.return_value = None

        with pytest.raises(CompanyNotFoundError):
            handler.handle(
                ActivateSubscriptionCommand(
                    stripe_customer_id="cus_missing",
                    stripe_subscription_id="sub_123",
                    plan=PlanTier.PREMIUM,
                    current_period_end=datetime(2026, 4, 1, tzinfo=timezone.utc),
                )
            )
