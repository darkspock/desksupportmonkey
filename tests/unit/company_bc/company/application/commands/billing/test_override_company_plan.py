from unittest.mock import MagicMock

import pytest

from src.company_bc.company.application.commands.billing.override_company_plan import (
    CompanyNotFoundError,
    OverrideCompanyPlanCommand,
    OverrideCompanyPlanCommandHandler,
)
from src.company_bc.company.domain.billing_enums import BillingStatus, PlanTier
from src.company_bc.company.domain.entities import Company


@pytest.fixture
def handler():
    return OverrideCompanyPlanCommandHandler(company_repo=MagicMock())


class TestOverrideCompanyPlan:
    def test_overrides_plan_and_sets_active(self, handler):
        company = Company.create(name="Acme", email_domains=["acme.com"])
        company.plan = PlanTier.FREE
        company.billing_status = BillingStatus.SUSPENDED
        handler.company_repo.find_by_id.return_value = company

        handler.handle(OverrideCompanyPlanCommand(company_id="cid", new_plan=PlanTier.PREMIUM))

        assert company.plan == PlanTier.PREMIUM
        assert company.billing_status == BillingStatus.ACTIVE
        handler.company_repo.save.assert_called_once_with(company)

    def test_company_not_found_raises(self, handler):
        handler.company_repo.find_by_id.return_value = None

        with pytest.raises(CompanyNotFoundError):
            handler.handle(OverrideCompanyPlanCommand(company_id="missing", new_plan=PlanTier.ENTERPRISE))
