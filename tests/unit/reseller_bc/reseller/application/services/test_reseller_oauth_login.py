from unittest.mock import MagicMock

import pytest

from src.reseller_bc.reseller.application.services.reseller_oauth_login import (
    OAuthUserInfo,
    ResellerOAuthLoginService,
)
from src.reseller_bc.reseller.domain.entities import Reseller
from src.reseller_bc.reseller.domain.enums import ResellerStatus
from src.reseller_bc.reseller.domain.exceptions import (
    ResellerDeactivatedException,
    ResellerNotRegisteredException,
)


class TestResellerOAuthLoginService:
    def setup_method(self):
        self.repo = MagicMock()
        self.jwt_service = MagicMock()
        self.jwt_service.create_token.return_value = "test-jwt-token"
        self.service = ResellerOAuthLoginService(
            repo=self.repo,
            jwt_service=self.jwt_service,
        )

    def _make_reseller(self, status=ResellerStatus.ACTIVE) -> Reseller:
        return Reseller(
            id="reseller-123",
            email="partner@example.com",
            name="Partner Inc",
            commission_pct=20,
            min_payout_cents=5000,
            referral_code="abc12345",
            status=status,
        )

    def _make_info(self, provider_field="google_id") -> OAuthUserInfo:
        return OAuthUserInfo(
            email="partner@example.com",
            name="Partner Inc",
            provider_id="google-sub-123",
            provider_field=provider_field,
        )

    def test_login_by_provider(self):
        reseller = self._make_reseller()
        self.repo.find_by_google_id.return_value = reseller

        token = self.service.login(self._make_info())

        assert token == "test-jwt-token"
        self.jwt_service.create_token.assert_called_once_with(
            user_id="reseller-123",
            company_id=None,
            role="reseller",
            type="reseller",
        )
        self.repo.save.assert_called_once()

    def test_login_fallback_to_email(self):
        reseller = self._make_reseller()
        self.repo.find_by_google_id.return_value = None
        self.repo.find_by_email.return_value = reseller

        token = self.service.login(self._make_info())

        assert token == "test-jwt-token"
        self.repo.find_by_email.assert_called_once_with("partner@example.com")

    def test_login_not_registered(self):
        self.repo.find_by_google_id.return_value = None
        self.repo.find_by_email.return_value = None

        with pytest.raises(ResellerNotRegisteredException):
            self.service.login(self._make_info())

    def test_login_deactivated(self):
        reseller = self._make_reseller(status=ResellerStatus.DEACTIVATED)
        self.repo.find_by_google_id.return_value = reseller

        with pytest.raises(ResellerDeactivatedException):
            self.service.login(self._make_info())

    def test_login_suspended_allowed(self):
        reseller = self._make_reseller(status=ResellerStatus.SUSPENDED)
        self.repo.find_by_google_id.return_value = reseller

        token = self.service.login(self._make_info())

        assert token == "test-jwt-token"

    def test_login_links_provider_on_first_use(self):
        reseller = self._make_reseller()
        assert reseller.google_id is None
        self.repo.find_by_email.return_value = reseller
        self.repo.find_by_google_id.return_value = None

        self.service.login(self._make_info())

        assert reseller.google_id == "google-sub-123"
        self.repo.save.assert_called_once()

    def test_login_microsoft_provider(self):
        reseller = self._make_reseller()
        self.repo.find_by_microsoft_id.return_value = reseller
        info = OAuthUserInfo(
            email="partner@example.com",
            name="Partner",
            provider_id="ms-oid-123",
            provider_field="microsoft_id",
        )

        self.service.login(info)

        assert reseller.microsoft_id == "ms-oid-123"
