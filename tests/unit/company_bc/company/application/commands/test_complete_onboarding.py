from unittest.mock import MagicMock

import pytest

from src.company_bc.company.application.commands.complete_onboarding import (
    CompanyNotFoundError,
    CompleteOnboardingCommand,
    CompleteOnboardingCommandHandler,
)
from src.company_bc.company.domain.entities import Company, InvalidSectorError


@pytest.fixture
def handler():
    return CompleteOnboardingCommandHandler(company_repo=MagicMock())


@pytest.fixture
def existing_company():
    return Company.create(name="Acme Corp", email_domains=["acme.com"])


class TestCompleteOnboardingCommand:
    def test_happy_path_with_sector(self, handler, existing_company):
        handler.company_repo.find_by_id.return_value = existing_company

        handler.handle(
            CompleteOnboardingCommand(
                company_id=existing_company.id,
                sector="financial_services",
            )
        )

        assert existing_company.sector == "financial_services"
        assert existing_company.onboarding_completed_at is not None
        handler.company_repo.save.assert_called_once()

    def test_skip_sector_none(self, handler, existing_company):
        handler.company_repo.find_by_id.return_value = existing_company

        handler.handle(
            CompleteOnboardingCommand(
                company_id=existing_company.id,
                sector=None,
            )
        )

        assert existing_company.sector is None
        assert existing_company.onboarding_completed_at is not None
        handler.company_repo.save.assert_called_once()

    def test_company_not_found_raises(self, handler):
        handler.company_repo.find_by_id.return_value = None

        with pytest.raises(CompanyNotFoundError):
            handler.handle(
                CompleteOnboardingCommand(company_id="nonexistent")
            )

    def test_invalid_sector_raises(self, handler, existing_company):
        handler.company_repo.find_by_id.return_value = existing_company

        with pytest.raises(InvalidSectorError):
            handler.handle(
                CompleteOnboardingCommand(
                    company_id=existing_company.id,
                    sector="invalid_sector",
                )
            )

    def test_idempotent_second_call(self, handler, existing_company):
        handler.company_repo.find_by_id.return_value = existing_company

        handler.handle(
            CompleteOnboardingCommand(
                company_id=existing_company.id,
                sector="technology",
            )
        )
        first_ts = existing_company.onboarding_completed_at

        handler.handle(
            CompleteOnboardingCommand(
                company_id=existing_company.id,
                sector="healthcare",
            )
        )

        assert existing_company.sector == "healthcare"
        assert existing_company.onboarding_completed_at >= first_ts
