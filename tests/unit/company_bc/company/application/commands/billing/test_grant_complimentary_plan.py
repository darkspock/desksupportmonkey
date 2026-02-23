from unittest.mock import MagicMock

import pytest

from src.company_bc.company.application.commands.billing.grant_complimentary_plan import (
    CompanyNotFoundError,
    GrantComplimentaryPlanCommand,
    GrantComplimentaryPlanCommandHandler,
)
from src.company_bc.company.domain.billing_enums import BillingStatus, PlanTier
from src.company_bc.company.domain.entities import Company


@pytest.fixture
def handler():
    return GrantComplimentaryPlanCommandHandler(
        company_repo=MagicMock(),
        stripe_client=MagicMock(),
    )


class TestGrantComplimentaryPlan:
    def test_grants_complimentary_plan(self, handler):
        company = Company.create(name="Acme", email_domains=["acme.com"])
        company.plan = PlanTier.FREE
        company.stripe_subscription_id = None
        handler.company_repo.find_by_id.return_value = company

        handler.handle(GrantComplimentaryPlanCommand(company_id="cid", plan=PlanTier.ENTERPRISE))

        assert company.complimentary is True
        assert company.plan == PlanTier.ENTERPRISE
        assert company.billing_status == BillingStatus.ACTIVE
        handler.company_repo.save.assert_called_once_with(company)

    def test_cancels_active_stripe_subscription(self, handler):
        company = Company.create(name="Acme", email_domains=["acme.com"])
        company.stripe_subscription_id = "sub_xyz"
        handler.company_repo.find_by_id.return_value = company

        handler.handle(GrantComplimentaryPlanCommand(company_id="cid", plan=PlanTier.ENTERPRISE))

        handler.stripe_client.cancel_subscription.assert_called_once_with("sub_xyz")
        assert company.stripe_subscription_id is None

    def test_no_stripe_call_when_no_subscription(self, handler):
        company = Company.create(name="Acme", email_domains=["acme.com"])
        company.stripe_subscription_id = None
        handler.company_repo.find_by_id.return_value = company

        handler.handle(GrantComplimentaryPlanCommand(company_id="cid", plan=PlanTier.PREMIUM))

        handler.stripe_client.cancel_subscription.assert_not_called()

    def test_company_not_found_raises(self, handler):
        handler.company_repo.find_by_id.return_value = None

        with pytest.raises(CompanyNotFoundError):
            handler.handle(GrantComplimentaryPlanCommand(company_id="missing", plan=PlanTier.ENTERPRISE))
