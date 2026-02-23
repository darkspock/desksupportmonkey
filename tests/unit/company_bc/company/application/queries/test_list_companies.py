from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

from src.company_bc.company.application.queries.list_companies import (
    ListCompaniesQuery,
    ListCompaniesQueryHandler,
)
from src.company_bc.company.domain.entities import Company


def _make_company(**kwargs) -> Company:
    company = Company.create(name="Acme", email_domains=["acme.com"])
    for k, v in kwargs.items():
        setattr(company, k, v)
    return company


def _make_handler(rows, total=None):
    handler = ListCompaniesQueryHandler(company_repo=MagicMock())
    handler.company_repo.find_all_with_counts.return_value = (rows, total or len(rows))
    return handler


class TestListCompaniesQueryHandler:
    def test_company_in_trial_has_positive_trial_days_remaining(self):
        trial_end = datetime.now(timezone.utc) + timedelta(days=7)
        company = _make_company(trial_ends_at=trial_end)
        handler = _make_handler([(company, 3, 10)])

        items, _ = handler.handle(ListCompaniesQuery())

        assert items[0].trial_days_remaining is not None
        assert items[0].trial_days_remaining >= 6  # at least 6 days (timing tolerance)

    def test_company_with_expired_trial_has_null_trial_days_remaining(self):
        trial_end = datetime.now(timezone.utc) - timedelta(days=1)
        company = _make_company(trial_ends_at=trial_end)
        handler = _make_handler([(company, 0, 0)])

        items, _ = handler.handle(ListCompaniesQuery())

        assert items[0].trial_days_remaining is None

    def test_company_with_no_trial_ends_at_has_null_trial_days_remaining(self):
        company = _make_company(trial_ends_at=None)
        handler = _make_handler([(company, 0, 0)])

        items, _ = handler.handle(ListCompaniesQuery())

        assert items[0].trial_days_remaining is None

    def test_dto_includes_plan_and_billing_status_from_entity(self):
        from src.company_bc.company.domain.billing_enums import BillingStatus, PlanTier

        company = _make_company(
            trial_ends_at=None,
            plan=PlanTier.PREMIUM,
            billing_status=BillingStatus.ACTIVE,
        )
        handler = _make_handler([(company, 5, 20)])

        items, _ = handler.handle(ListCompaniesQuery())

        assert items[0].plan == PlanTier.PREMIUM
        assert items[0].billing_status == BillingStatus.ACTIVE

    def test_dto_includes_user_and_asset_counts(self):
        company = _make_company(trial_ends_at=None)
        handler = _make_handler([(company, 7, 42)])

        items, _ = handler.handle(ListCompaniesQuery())

        assert items[0].user_count == 7
        assert items[0].asset_count == 42

    def test_handler_passes_in_trial_filter_to_repository(self):
        handler = _make_handler([])

        handler.handle(ListCompaniesQuery(in_trial=True, plan="premium"))

        handler.company_repo.find_all_with_counts.assert_called_once_with(
            page=1, page_size=20, search=None, in_trial=True, plan="premium"
        )

    def test_pagination_total_returned_correctly(self):
        companies = [_make_company(trial_ends_at=None) for _ in range(3)]
        handler = _make_handler([(c, 0, 0) for c in companies], total=50)

        items, total = handler.handle(ListCompaniesQuery(page=2, page_size=3))

        assert len(items) == 3
        assert total == 50
