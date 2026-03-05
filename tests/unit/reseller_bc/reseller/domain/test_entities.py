import pytest

from src.reseller_bc.reseller.domain.entities import Reseller
from src.reseller_bc.reseller.domain.enums import ResellerStatus
from src.reseller_bc.reseller.domain.exceptions import (
    InvalidCommissionRateException,
    InvalidMinPayoutException,
    ResellerOAuthProviderAlreadyLinkedError,
)


class TestResellerCreate:
    def test_create_happy_path(self):
        reseller = Reseller.create(
            email="partner@example.com",
            name="Partner Inc",
            commission_pct=20,
            min_payout_cents=5000,
        )
        assert reseller.email == "partner@example.com"
        assert reseller.name == "Partner Inc"
        assert reseller.commission_pct == 20
        assert reseller.min_payout_cents == 5000
        assert reseller.status == ResellerStatus.ACTIVE
        assert len(reseller.referral_code) == 8
        assert reseller.id  # ULID generated

    def test_create_with_custom_id(self):
        reseller = Reseller.create(
            id="custom-id-123",
            email="test@example.com",
            name="Test",
            commission_pct=10,
            min_payout_cents=1000,
        )
        assert reseller.id == "custom-id-123"

    def test_create_normalizes_email(self):
        reseller = Reseller.create(
            email="  PARTNER@Example.COM  ",
            name="Test",
            commission_pct=10,
            min_payout_cents=1000,
        )
        assert reseller.email == "partner@example.com"

    def test_create_strips_name(self):
        reseller = Reseller.create(
            email="test@example.com",
            name="  Partner Inc  ",
            commission_pct=10,
            min_payout_cents=1000,
        )
        assert reseller.name == "Partner Inc"

    def test_create_invalid_email_empty(self):
        with pytest.raises(ValueError, match="Invalid email"):
            Reseller.create(email="", name="Test", commission_pct=10, min_payout_cents=1000)

    def test_create_invalid_email_no_at(self):
        with pytest.raises(ValueError, match="Invalid email"):
            Reseller.create(email="invalid", name="Test", commission_pct=10, min_payout_cents=1000)

    def test_create_empty_name(self):
        with pytest.raises(ValueError, match="Name is required"):
            Reseller.create(email="test@example.com", name="", commission_pct=10, min_payout_cents=1000)

    def test_create_whitespace_name(self):
        with pytest.raises(ValueError, match="Name is required"):
            Reseller.create(email="test@example.com", name="   ", commission_pct=10, min_payout_cents=1000)

    def test_create_commission_pct_negative(self):
        with pytest.raises(InvalidCommissionRateException):
            Reseller.create(email="t@e.com", name="T", commission_pct=-1, min_payout_cents=1000)

    def test_create_commission_pct_over_100(self):
        with pytest.raises(InvalidCommissionRateException):
            Reseller.create(email="t@e.com", name="T", commission_pct=101, min_payout_cents=1000)

    def test_create_commission_pct_boundary_0(self):
        reseller = Reseller.create(email="t@e.com", name="T", commission_pct=0, min_payout_cents=1000)
        assert reseller.commission_pct == 0

    def test_create_commission_pct_boundary_100(self):
        reseller = Reseller.create(email="t@e.com", name="T", commission_pct=100, min_payout_cents=1000)
        assert reseller.commission_pct == 100

    def test_create_min_payout_zero(self):
        with pytest.raises(InvalidMinPayoutException):
            Reseller.create(email="t@e.com", name="T", commission_pct=10, min_payout_cents=0)

    def test_create_min_payout_negative(self):
        with pytest.raises(InvalidMinPayoutException):
            Reseller.create(email="t@e.com", name="T", commission_pct=10, min_payout_cents=-100)


class TestResellerUpdateProfile:
    def test_update_profile(self):
        reseller = Reseller.create(email="t@e.com", name="T", commission_pct=10, min_payout_cents=1000)
        reseller.update_profile(company_name="Acme Corp", tax_id="123-456")
        assert reseller.company_name == "Acme Corp"
        assert reseller.tax_id == "123-456"

    def test_update_profile_partial(self):
        reseller = Reseller.create(email="t@e.com", name="T", commission_pct=10, min_payout_cents=1000)
        reseller.company_name = "Old Name"
        reseller.update_profile(company_name="New Name")
        assert reseller.company_name == "New Name"
        assert reseller.tax_id is None  # unchanged (None was not passed)

    def test_update_profile_clear_with_empty_string(self):
        reseller = Reseller.create(email="t@e.com", name="T", commission_pct=10, min_payout_cents=1000)
        reseller.company_name = "Old"
        reseller.update_profile(company_name="")
        assert reseller.company_name is None


class TestResellerUpdateSettings:
    def test_update_settings(self):
        reseller = Reseller.create(email="t@e.com", name="T", commission_pct=10, min_payout_cents=1000)
        reseller.update_settings(commission_pct=25, min_payout_cents=10000)
        assert reseller.commission_pct == 25
        assert reseller.min_payout_cents == 10000

    def test_update_settings_invalid_commission(self):
        reseller = Reseller.create(email="t@e.com", name="T", commission_pct=10, min_payout_cents=1000)
        with pytest.raises(InvalidCommissionRateException):
            reseller.update_settings(commission_pct=150)

    def test_update_settings_invalid_min_payout(self):
        reseller = Reseller.create(email="t@e.com", name="T", commission_pct=10, min_payout_cents=1000)
        with pytest.raises(InvalidMinPayoutException):
            reseller.update_settings(min_payout_cents=0)

    def test_update_settings_with_status(self):
        reseller = Reseller.create(email="t@e.com", name="T", commission_pct=10, min_payout_cents=1000)
        reseller.update_settings(status=ResellerStatus.SUSPENDED)
        assert reseller.status == ResellerStatus.SUSPENDED


class TestResellerStatusTransitions:
    def test_suspend_from_active(self):
        reseller = Reseller.create(email="t@e.com", name="T", commission_pct=10, min_payout_cents=1000)
        assert reseller.status == ResellerStatus.ACTIVE
        reseller.suspend()
        assert reseller.status == ResellerStatus.SUSPENDED

    def test_activate_from_suspended(self):
        reseller = Reseller.create(email="t@e.com", name="T", commission_pct=10, min_payout_cents=1000)
        reseller.suspend()
        reseller.activate()
        assert reseller.status == ResellerStatus.ACTIVE

    def test_deactivate_from_active(self):
        reseller = Reseller.create(email="t@e.com", name="T", commission_pct=10, min_payout_cents=1000)
        reseller.deactivate()
        assert reseller.status == ResellerStatus.DEACTIVATED

    def test_deactivate_from_suspended(self):
        reseller = Reseller.create(email="t@e.com", name="T", commission_pct=10, min_payout_cents=1000)
        reseller.suspend()
        reseller.deactivate()
        assert reseller.status == ResellerStatus.DEACTIVATED


class TestResellerOAuthLinking:
    def test_link_google(self):
        reseller = Reseller.create(email="t@e.com", name="T", commission_pct=10, min_payout_cents=1000)
        reseller.link_google("google-123")
        assert reseller.google_id == "google-123"

    def test_link_google_same_id(self):
        reseller = Reseller.create(email="t@e.com", name="T", commission_pct=10, min_payout_cents=1000)
        reseller.link_google("google-123")
        reseller.link_google("google-123")  # same ID, no error
        assert reseller.google_id == "google-123"

    def test_link_google_different_id_raises(self):
        reseller = Reseller.create(email="t@e.com", name="T", commission_pct=10, min_payout_cents=1000)
        reseller.link_google("google-123")
        with pytest.raises(ResellerOAuthProviderAlreadyLinkedError):
            reseller.link_google("google-456")

    def test_link_microsoft(self):
        reseller = Reseller.create(email="t@e.com", name="T", commission_pct=10, min_payout_cents=1000)
        reseller.link_microsoft("ms-123")
        assert reseller.microsoft_id == "ms-123"

    def test_link_microsoft_different_id_raises(self):
        reseller = Reseller.create(email="t@e.com", name="T", commission_pct=10, min_payout_cents=1000)
        reseller.link_microsoft("ms-123")
        with pytest.raises(ResellerOAuthProviderAlreadyLinkedError):
            reseller.link_microsoft("ms-456")
