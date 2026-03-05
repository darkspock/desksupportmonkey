from unittest.mock import MagicMock

import pytest

from src.reseller_bc.reseller.application.commands.password_login import (
    ResellerPasswordLoginService,
)
from src.reseller_bc.reseller.domain.entities import Reseller
from src.reseller_bc.reseller.domain.enums import ResellerStatus
from src.reseller_bc.reseller.domain.exceptions import (
    ResellerDeactivatedException,
    ResellerInvalidPasswordException,
    ResellerNotRegisteredException,
    ResellerPendingApprovalException,
)


def _make_reseller(status=ResellerStatus.ACTIVE, password_hash="hashed", **kwargs):
    return Reseller(
        id="res-1",
        email="partner@example.com",
        name="Partner Inc",
        commission_pct=20,
        min_payout_cents=5000,
        referral_code="abc12345",
        status=status,
        password_hash=password_hash,
        **kwargs,
    )


class TestResellerPasswordLoginService:
    def setup_method(self):
        self.repo = MagicMock()
        self.password_service = MagicMock()
        self.jwt_service = MagicMock()
        self.jwt_service.create_token.return_value = "jwt-token"
        self.service = ResellerPasswordLoginService(
            repo=self.repo,
            password_service=self.password_service,
            jwt_service=self.jwt_service,
        )

    def test_login_success(self):
        reseller = _make_reseller()
        self.repo.find_by_email.return_value = reseller
        self.password_service.verify_password.return_value = True

        token = self.service.login("partner@example.com", "password123")

        assert token == "jwt-token"
        self.jwt_service.create_token.assert_called_once_with(
            user_id="res-1",
            company_id=None,
            role="reseller",
            type="reseller",
        )

    def test_login_email_not_found(self):
        self.repo.find_by_email.return_value = None

        with pytest.raises(ResellerNotRegisteredException):
            self.service.login("unknown@example.com", "password123")

    def test_login_wrong_password(self):
        reseller = _make_reseller()
        self.repo.find_by_email.return_value = reseller
        self.password_service.verify_password.return_value = False

        with pytest.raises(ResellerInvalidPasswordException):
            self.service.login("partner@example.com", "wrongpassword")

    def test_login_pending_account(self):
        reseller = _make_reseller(status=ResellerStatus.PENDING)
        self.repo.find_by_email.return_value = reseller
        self.password_service.verify_password.return_value = True

        with pytest.raises(ResellerPendingApprovalException):
            self.service.login("partner@example.com", "password123")

    def test_login_deactivated_account(self):
        reseller = _make_reseller(status=ResellerStatus.DEACTIVATED)
        self.repo.find_by_email.return_value = reseller
        self.password_service.verify_password.return_value = True

        with pytest.raises(ResellerDeactivatedException):
            self.service.login("partner@example.com", "password123")

    def test_login_oauth_only_account(self):
        reseller = _make_reseller(password_hash=None)
        self.repo.find_by_email.return_value = reseller

        with pytest.raises(ResellerInvalidPasswordException):
            self.service.login("partner@example.com", "password123")
