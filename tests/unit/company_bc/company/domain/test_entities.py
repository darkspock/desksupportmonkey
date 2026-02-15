import pytest

from src.company_bc.company.domain.entities import Company
from src.company_bc.company.domain.enums import CompanyStatus


class TestCompanyCreate:
    def test_create_with_valid_data(self):
        company = Company.create(name="Acme Corp", email_domains=["acme.com"])
        assert company.name == "Acme Corp"
        assert company.status == CompanyStatus.ACTIVE
        assert company.is_active is True
        assert company.email_domains == ["acme.com"]
        assert len(company.id) == 26

    def test_create_with_multiple_domains(self):
        company = Company.create(
            name="Acme Corp", email_domains=["acme.com", "acme.co.uk"]
        )
        assert company.email_domains == ["acme.com", "acme.co.uk"]

    def test_create_normalizes_domains_to_lowercase(self):
        company = Company.create(name="Acme", email_domains=["ACME.COM", " Acme.Co.UK "])
        assert company.email_domains == ["acme.com", "acme.co.uk"]

    def test_create_strips_name(self):
        company = Company.create(name="  Acme Corp  ", email_domains=["acme.com"])
        assert company.name == "Acme Corp"

    def test_create_with_empty_name_raises(self):
        with pytest.raises(ValueError, match="Company name is required"):
            Company.create(name="", email_domains=["acme.com"])

    def test_create_with_whitespace_name_raises(self):
        with pytest.raises(ValueError, match="Company name is required"):
            Company.create(name="   ", email_domains=["acme.com"])

    def test_create_with_no_domains_raises(self):
        with pytest.raises(ValueError, match="At least one email domain"):
            Company.create(name="Acme", email_domains=[])


class TestCompanyUpdate:
    def test_update_name(self):
        company = Company.create(name="Old Name", email_domains=["old.com"])
        company.update(name="New Name")
        assert company.name == "New Name"

    def test_update_domains(self):
        company = Company.create(name="Acme", email_domains=["old.com"])
        company.update(email_domains=["new.com", "new.co.uk"])
        assert company.email_domains == ["new.com", "new.co.uk"]

    def test_update_name_and_domains(self):
        company = Company.create(name="Old", email_domains=["old.com"])
        company.update(name="New", email_domains=["new.com"])
        assert company.name == "New"
        assert company.email_domains == ["new.com"]

    def test_update_with_empty_name_raises(self):
        company = Company.create(name="Acme", email_domains=["acme.com"])
        with pytest.raises(ValueError, match="Company name is required"):
            company.update(name="")

    def test_update_with_empty_domains_raises(self):
        company = Company.create(name="Acme", email_domains=["acme.com"])
        with pytest.raises(ValueError, match="At least one email domain"):
            company.update(email_domains=[])

    def test_update_none_values_no_change(self):
        company = Company.create(name="Acme", email_domains=["acme.com"])
        company.update(name=None, email_domains=None)
        assert company.name == "Acme"
        assert company.email_domains == ["acme.com"]
