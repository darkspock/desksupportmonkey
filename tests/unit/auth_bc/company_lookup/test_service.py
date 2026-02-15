from unittest.mock import MagicMock

from src.auth_bc.company_lookup.infrastructure.service import CompanyLookupService


class TestCompanyLookupService:
    def test_find_company_by_domain_active(self):
        session = MagicMock()
        session.execute.return_value.first.return_value = ("company-123", True)

        service = CompanyLookupService(session)
        result = service.find_company_by_email_domain("user@acme.com")

        assert result == ("company-123", True)

    def test_find_company_by_domain_inactive(self):
        session = MagicMock()
        session.execute.return_value.first.return_value = ("company-123", False)

        service = CompanyLookupService(session)
        result = service.find_company_by_email_domain("user@suspended.com")

        assert result == ("company-123", False)

    def test_find_company_by_domain_not_found(self):
        session = MagicMock()
        session.execute.return_value.first.return_value = None

        service = CompanyLookupService(session)
        result = service.find_company_by_email_domain("user@unknown.com")

        assert result is None

    def test_find_company_id_active_returns_id(self):
        session = MagicMock()
        session.execute.return_value.first.return_value = ("company-123", True)

        service = CompanyLookupService(session)
        result = service.find_company_id_by_email_domain("user@acme.com")

        assert result == "company-123"

    def test_find_company_id_inactive_returns_none(self):
        session = MagicMock()
        session.execute.return_value.first.return_value = ("company-123", False)

        service = CompanyLookupService(session)
        result = service.find_company_id_by_email_domain("user@suspended.com")

        assert result is None
