from unittest.mock import MagicMock

import pytest

from src.company_bc.company.application.commands.billing.revoke_complimentary_plan import (
    CompanyNotFoundError,
    RevokeComplimentaryPlanCommand,
    RevokeComplimentaryPlanCommandHandler,
)
from src.company_bc.company.domain.billing_enums import BillingStatus, PlanTier
from src.company_bc.company.domain.entities import Company


@pytest.fixture
def handler():
    return RevokeComplimentaryPlanCommandHandler(company_repo=MagicMock())


class TestRevokeComplimentaryPlan:
    def test_revokes_complimentary_sets_free_over_limit(self, handler):
        company = Company.create(name="Acme", email_domains=["acme.com"])
        company.complimentary = True
        company.plan = PlanTier.ENTERPRISE
        company.billing_status = BillingStatus.ACTIVE
        handler.company_repo.find_by_id.return_value = company

        handler.handle(RevokeComplimentaryPlanCommand(company_id="cid"))

        assert company.complimentary is False
        assert company.plan == PlanTier.FREE
        assert company.billing_status == BillingStatus.OVER_LIMIT
        handler.company_repo.save.assert_called_once_with(company)

    def test_not_complimentary_raises_value_error(self, handler):
        company = Company.create(name="Acme", email_domains=["acme.com"])
        company.complimentary = False
        handler.company_repo.find_by_id.return_value = company

        with pytest.raises(ValueError, match="not on complimentary"):
            handler.handle(RevokeComplimentaryPlanCommand(company_id="cid"))

    def test_company_not_found_raises(self, handler):
        handler.company_repo.find_by_id.return_value = None

        with pytest.raises(CompanyNotFoundError):
            handler.handle(RevokeComplimentaryPlanCommand(company_id="missing"))
