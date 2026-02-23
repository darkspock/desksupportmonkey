from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from src.company_bc.company.application.queries.billing.get_company_billing import (
    CompanyNotFoundError,
    GetCompanyBillingQuery,
    GetCompanyBillingQueryHandler,
)
from src.company_bc.company.domain.entities import Company


def _make_company(**kwargs) -> Company:
    company = Company.create(name="Acme", email_domains=["acme.com"])
    for k, v in kwargs.items():
        setattr(company, k, v)
    return company


def _make_handler(company):
    handler = GetCompanyBillingQueryHandler(company_repo=MagicMock())
    handler.company_repo.find_by_id.return_value = company
    return handler


class TestGetCompanyBillingQueryHandler:
    def test_company_in_trial_has_trial_days_remaining_and_trial_ends_at(self):
        trial_end = datetime.now(timezone.utc) + timedelta(days=10)
        company = _make_company(trial_ends_at=trial_end)
        handler = _make_handler(company)

        dto = handler.handle(GetCompanyBillingQuery(company_id=company.id))

        assert dto.trial_days_remaining is not None
        assert dto.trial_days_remaining >= 9
        assert dto.trial_ends_at == trial_end

    def test_company_not_in_trial_has_null_trial_fields(self):
        company = _make_company(trial_ends_at=None)
        handler = _make_handler(company)

        dto = handler.handle(GetCompanyBillingQuery(company_id=company.id))

        assert dto.trial_days_remaining is None
        assert dto.trial_ends_at is None

    def test_company_with_expired_trial_has_null_trial_days_remaining(self):
        trial_end = datetime.now(timezone.utc) - timedelta(days=1)
        company = _make_company(trial_ends_at=trial_end)
        handler = _make_handler(company)

        dto = handler.handle(GetCompanyBillingQuery(company_id=company.id))

        assert dto.trial_days_remaining is None

    def test_not_found_raises(self):
        handler = GetCompanyBillingQueryHandler(company_repo=MagicMock())
        handler.company_repo.find_by_id.return_value = None

        with pytest.raises(CompanyNotFoundError):
            handler.handle(GetCompanyBillingQuery(company_id="nonexistent"))
