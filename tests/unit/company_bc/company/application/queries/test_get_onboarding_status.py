from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from src.company_bc.company.application.queries.get_onboarding_status import (
    CompanyNotFoundError,
    GetOnboardingStatusQuery,
    GetOnboardingStatusQueryHandler,
)
from src.company_bc.company.domain.entities import Company


@pytest.fixture
def handler():
    return GetOnboardingStatusQueryHandler(company_repo=MagicMock())


@pytest.fixture
def existing_company():
    return Company.create(name="Acme Corp", email_domains=["acme.com"])


class TestGetOnboardingStatusQuery:
    def test_needs_onboarding_when_not_completed(self, handler, existing_company):
        handler.company_repo.find_by_id.return_value = existing_company

        result = handler.handle(
            GetOnboardingStatusQuery(company_id=existing_company.id)
        )

        assert result.needs_onboarding is True
        assert result.onboarding_completed_at is None
        assert result.sector is None

    def test_does_not_need_onboarding_when_completed(self, handler, existing_company):
        existing_company.complete_onboarding()
        existing_company.set_sector("technology")
        handler.company_repo.find_by_id.return_value = existing_company

        result = handler.handle(
            GetOnboardingStatusQuery(company_id=existing_company.id)
        )

        assert result.needs_onboarding is False
        assert result.onboarding_completed_at is not None
        assert result.sector == "technology"

    def test_returns_sector_value(self, handler, existing_company):
        existing_company.sector = "healthcare"
        handler.company_repo.find_by_id.return_value = existing_company

        result = handler.handle(
            GetOnboardingStatusQuery(company_id=existing_company.id)
        )

        assert result.sector == "healthcare"

    def test_company_not_found_raises(self, handler):
        handler.company_repo.find_by_id.return_value = None

        with pytest.raises(CompanyNotFoundError):
            handler.handle(
                GetOnboardingStatusQuery(company_id="nonexistent")
            )
