from unittest.mock import MagicMock

import pytest

from src.company_bc.company.application.queries.get_company_by_slug import (
    CompanyBySlugDto,
    CompanyNotFoundError,
    GetCompanyBySlugQuery,
    GetCompanyBySlugQueryHandler,
)
from src.company_bc.company.domain.entities import Company
from src.company_bc.company.domain.enums import AuthMode, CompanyStatus


def _make_company(slug="acme-corp", is_active=True) -> Company:
    company = Company.create(name="Acme Corp", email_domains=["acme.com"])
    company.slug = slug
    company.auth_mode = AuthMode.DOMAIN
    if not is_active:
        company.change_status(CompanyStatus.DEACTIVATED)
    return company


@pytest.fixture
def oauth_settings():
    mock = MagicMock()
    mock.GOOGLE_CLIENT_ID = "google-id"
    mock.MICROSOFT_CLIENT_ID = "microsoft-id"
    return mock


@pytest.fixture
def handler(oauth_settings):
    return GetCompanyBySlugQueryHandler(
        company_repo=MagicMock(),
        oauth_settings=oauth_settings,
    )


class TestGetCompanyBySlugQuery:
    def test_success_returns_dto(self, handler):
        company = _make_company()
        handler.company_repo.find_by_slug.return_value = company

        result = handler.handle(GetCompanyBySlugQuery(slug="acme-corp"))

        assert isinstance(result, CompanyBySlugDto)
        assert result.id == company.id
        assert result.name == "Acme Corp"
        assert result.slug == "acme-corp"
        assert result.auth_mode == "domain"
        assert result.google_enabled is True
        assert result.microsoft_enabled is True

    def test_company_not_found_raises(self, handler):
        handler.company_repo.find_by_slug.return_value = None

        with pytest.raises(CompanyNotFoundError):
            handler.handle(GetCompanyBySlugQuery(slug="nonexistent"))

    def test_deactivated_company_raises(self, handler):
        company = _make_company(is_active=False)
        handler.company_repo.find_by_slug.return_value = company

        with pytest.raises(CompanyNotFoundError):
            handler.handle(GetCompanyBySlugQuery(slug="acme-corp"))

    def test_google_only(self, handler, oauth_settings):
        oauth_settings.GOOGLE_CLIENT_ID = "google-id"
        oauth_settings.MICROSOFT_CLIENT_ID = ""
        company = _make_company()
        handler.company_repo.find_by_slug.return_value = company

        result = handler.handle(GetCompanyBySlugQuery(slug="acme-corp"))

        assert result.google_enabled is True
        assert result.microsoft_enabled is False

    def test_no_oauth_providers(self, handler, oauth_settings):
        oauth_settings.GOOGLE_CLIENT_ID = ""
        oauth_settings.MICROSOFT_CLIENT_ID = ""
        company = _make_company()
        handler.company_repo.find_by_slug.return_value = company

        result = handler.handle(GetCompanyBySlugQuery(slug="acme-corp"))

        assert result.google_enabled is False
        assert result.microsoft_enabled is False

    def test_membership_only_mode(self, handler):
        company = _make_company()
        company.auth_mode = AuthMode.MEMBERSHIP_ONLY
        handler.company_repo.find_by_slug.return_value = company

        result = handler.handle(GetCompanyBySlugQuery(slug="acme-corp"))

        assert result.auth_mode == "membership_only"
