import pytest

from src.company_bc.company.domain.entities import Company, InvalidStatusTransitionError
from src.company_bc.company.domain.enums import CompanyStatus


@pytest.fixture
def active_company():
    return Company.create(name="Acme", email_domains=["acme.com"])


@pytest.fixture
def suspended_company():
    c = Company.create(name="Suspended Co", email_domains=["s.com"])
    c.change_status(CompanyStatus.SUSPENDED)
    return c


class TestCompanyStatusTransitions:
    def test_active_to_suspended(self, active_company):
        active_company.change_status(CompanyStatus.SUSPENDED)
        assert active_company.status == CompanyStatus.SUSPENDED
        assert active_company.is_active is False

    def test_active_to_deactivated(self, active_company):
        active_company.change_status(CompanyStatus.DEACTIVATED)
        assert active_company.status == CompanyStatus.DEACTIVATED
        assert active_company.is_active is False

    def test_suspended_to_active(self, suspended_company):
        suspended_company.change_status(CompanyStatus.ACTIVE)
        assert suspended_company.status == CompanyStatus.ACTIVE
        assert suspended_company.is_active is True

    def test_suspended_to_deactivated(self, suspended_company):
        suspended_company.change_status(CompanyStatus.DEACTIVATED)
        assert suspended_company.status == CompanyStatus.DEACTIVATED
        assert suspended_company.is_active is False

    def test_deactivated_to_active_raises(self):
        c = Company.create(name="D", email_domains=["d.com"])
        c.change_status(CompanyStatus.DEACTIVATED)
        with pytest.raises(InvalidStatusTransitionError, match="Cannot transition"):
            c.change_status(CompanyStatus.ACTIVE)

    def test_deactivated_to_suspended_raises(self):
        c = Company.create(name="D", email_domains=["d.com"])
        c.change_status(CompanyStatus.DEACTIVATED)
        with pytest.raises(InvalidStatusTransitionError, match="Cannot transition"):
            c.change_status(CompanyStatus.SUSPENDED)

    def test_same_status_raises(self, active_company):
        with pytest.raises(InvalidStatusTransitionError, match="already active"):
            active_company.change_status(CompanyStatus.ACTIVE)

    def test_is_active_syncs_on_reactivation(self, suspended_company):
        assert suspended_company.is_active is False
        suspended_company.change_status(CompanyStatus.ACTIVE)
        assert suspended_company.is_active is True
