from unittest.mock import MagicMock

import pytest

from src.company_bc.company.application.commands.billing.restore_billing import (
    CompanyNotFoundError,
    RestoreBillingCommand,
    RestoreBillingCommandHandler,
)
from src.company_bc.company.domain.billing_enums import BillingStatus
from src.company_bc.company.domain.entities import Company


@pytest.fixture
def handler():
    return RestoreBillingCommandHandler(company_repo=MagicMock())


class TestRestoreBilling:
    def test_restores_from_grace_period(self, handler):
        company = Company.create(name="Acme", email_domains=["acme.com"])
        company.enter_grace_period()
        handler.company_repo.find_by_stripe_customer_id.return_value = company

        handler.handle(RestoreBillingCommand(stripe_customer_id="cus_abc"))

        assert company.billing_status == BillingStatus.ACTIVE
        assert company.grace_period_started_at is None
        handler.company_repo.save.assert_called_once_with(company)

    def test_restores_from_suspended(self, handler):
        company = Company.create(name="Acme", email_domains=["acme.com"])
        company.set_billing_status(BillingStatus.SUSPENDED)
        handler.company_repo.find_by_stripe_customer_id.return_value = company

        handler.handle(RestoreBillingCommand(stripe_customer_id="cus_abc"))

        assert company.billing_status == BillingStatus.ACTIVE
        handler.company_repo.save.assert_called_once_with(company)

    def test_no_op_when_already_active(self, handler):
        company = Company.create(name="Acme", email_domains=["acme.com"])
        handler.company_repo.find_by_stripe_customer_id.return_value = company

        handler.handle(RestoreBillingCommand(stripe_customer_id="cus_abc"))

        handler.company_repo.save.assert_not_called()

    def test_company_not_found_raises(self, handler):
        handler.company_repo.find_by_stripe_customer_id.return_value = None

        with pytest.raises(CompanyNotFoundError):
            handler.handle(RestoreBillingCommand(stripe_customer_id="cus_missing"))
