from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from src.company_bc.company.application.queries.billing.get_billing_overview import (
    BillingOverviewDto,
    CompanyNotFoundError,
    GetBillingOverviewQuery,
    GetBillingOverviewQueryHandler,
)
from src.company_bc.company.domain.billing_enums import BillingStatus, PlanTier
from src.company_bc.company.domain.entities import Company


def _make_company(plan: PlanTier = PlanTier.FREE) -> Company:
    c = Company.create(name="Acme", email_domains=["acme.com"])
    c.plan = plan
    return c


@pytest.fixture
def handler():
    repo = MagicMock()
    repo.count_users.return_value = 3
    repo.count_assets.return_value = 12
    return GetBillingOverviewQueryHandler(company_repo=repo)


class TestGetBillingOverview:
    def test_returns_dto_with_counts_and_limits(self, handler):
        company = _make_company(PlanTier.FREE)
        handler.company_repo.find_by_id.return_value = company

        dto = handler.handle(GetBillingOverviewQuery(company_id="c1"))

        assert dto.plan == PlanTier.FREE
        assert dto.billing_status == BillingStatus.ACTIVE
        assert dto.user_count == 3
        assert dto.asset_count == 12
        assert dto.user_limit == 5
        assert dto.asset_limit == 50
        assert dto.grace_days_remaining is None
        assert dto.complimentary is False

    def test_premium_plan_limits(self, handler):
        company = _make_company(PlanTier.PREMIUM)
        handler.company_repo.find_by_id.return_value = company

        dto = handler.handle(GetBillingOverviewQuery(company_id="c1"))

        assert dto.user_limit == 25
        assert dto.asset_limit == 500

    def test_enterprise_plan_unlimited(self, handler):
        company = _make_company(PlanTier.ENTERPRISE)
        handler.company_repo.find_by_id.return_value = company

        dto = handler.handle(GetBillingOverviewQuery(company_id="c1"))

        assert dto.user_limit is None
        assert dto.asset_limit is None

    def test_grace_days_remaining_14_days_ago(self, handler):
        company = _make_company()
        company.enter_grace_period()
        # Simulate started 14 days ago
        company.grace_period_started_at = datetime.now(timezone.utc) - timedelta(days=14)
        handler.company_repo.find_by_id.return_value = company

        dto = handler.handle(GetBillingOverviewQuery(company_id="c1"))

        assert dto.grace_days_remaining == 1

    def test_grace_days_remaining_at_boundary(self, handler):
        """15 days elapsed → 0 days remaining."""
        company = _make_company()
        company.enter_grace_period()
        company.grace_period_started_at = datetime.now(timezone.utc) - timedelta(days=15)
        handler.company_repo.find_by_id.return_value = company

        dto = handler.handle(GetBillingOverviewQuery(company_id="c1"))

        assert dto.grace_days_remaining == 0

    def test_grace_days_clamped_to_zero_when_expired(self, handler):
        """More than 15 days elapsed → still 0, not negative."""
        company = _make_company()
        company.enter_grace_period()
        company.grace_period_started_at = datetime.now(timezone.utc) - timedelta(days=20)
        handler.company_repo.find_by_id.return_value = company

        dto = handler.handle(GetBillingOverviewQuery(company_id="c1"))

        assert dto.grace_days_remaining == 0

    def test_company_not_found_raises(self, handler):
        handler.company_repo.find_by_id.return_value = None

        with pytest.raises(CompanyNotFoundError):
            handler.handle(GetBillingOverviewQuery(company_id="missing"))
