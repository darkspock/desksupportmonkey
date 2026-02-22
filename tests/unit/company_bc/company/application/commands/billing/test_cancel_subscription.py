from unittest.mock import MagicMock

import pytest

from src.company_bc.company.application.commands.billing.cancel_subscription import (
    CancelSubscriptionCommand,
    CancelSubscriptionCommandHandler,
    CompanyNotFoundError,
)
from src.company_bc.company.domain.billing_enums import BillingStatus, PlanTier
from src.company_bc.company.domain.entities import Company


@pytest.fixture
def handler():
    return CancelSubscriptionCommandHandler(company_repo=MagicMock())


class TestCancelSubscription:
    def test_resets_to_free_plan(self, handler):
        company = Company.create(name="Acme", email_domains=["acme.com"])
        company.stripe_subscription_id = "sub_active"
        company.plan = PlanTier.PREMIUM
        handler.company_repo.find_by_stripe_customer_id.return_value = company

        handler.handle(CancelSubscriptionCommand(stripe_customer_id="cus_abc"))

        assert company.plan == PlanTier.FREE
        assert company.stripe_subscription_id is None
        assert company.billing_status == BillingStatus.ACTIVE
        assert company.pending_downgrade_plan is None
        handler.company_repo.save.assert_called_once_with(company)

    def test_company_not_found_raises(self, handler):
        handler.company_repo.find_by_stripe_customer_id.return_value = None

        with pytest.raises(CompanyNotFoundError):
            handler.handle(CancelSubscriptionCommand(stripe_customer_id="cus_missing"))
