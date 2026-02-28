import pytest

from src.company_bc.company.domain.entities import Company, InvalidSectorError


@pytest.fixture
def company():
    return Company.create(name="Test Corp", email_domains=["test.com"])


class TestSetSector:
    def test_valid_sector(self, company):
        company.set_sector("financial_services")
        assert company.sector == "financial_services"

    def test_all_valid_sectors(self, company):
        valid = [
            "financial_services", "healthcare", "government", "education",
            "technology", "manufacturing", "retail", "energy",
            "telecommunications", "professional_services", "logistics", "other",
        ]
        for sector in valid:
            company.set_sector(sector)
            assert company.sector == sector

    def test_invalid_sector_raises(self, company):
        with pytest.raises(InvalidSectorError):
            company.set_sector("invalid_value")

    def test_set_sector_none_clears(self, company):
        company.set_sector("technology")
        assert company.sector == "technology"
        company.set_sector(None)
        assert company.sector is None


class TestCompleteOnboarding:
    def test_sets_timestamp(self, company):
        assert company.onboarding_completed_at is None
        company.complete_onboarding()
        assert company.onboarding_completed_at is not None

    def test_idempotent(self, company):
        company.complete_onboarding()
        first = company.onboarding_completed_at
        company.complete_onboarding()
        assert company.onboarding_completed_at is not None
        assert company.onboarding_completed_at >= first
