from unittest.mock import MagicMock, patch

from src.reseller_bc.reseller.application.commands.forgot_password import (
    ForgotResellerPasswordCommand,
    ForgotResellerPasswordCommandHandler,
)
from src.reseller_bc.reseller.domain.entities import Reseller
from src.reseller_bc.reseller.domain.enums import ResellerStatus


def _make_reseller(password_hash="hashed"):
    return Reseller(
        id="res-1",
        email="partner@example.com",
        name="Partner Inc",
        commission_pct=20,
        min_payout_cents=5000,
        referral_code="abc12345",
        status=ResellerStatus.ACTIVE,
        password_hash=password_hash,
    )


class TestForgotResellerPasswordCommandHandler:
    def setup_method(self):
        self.repo = MagicMock()
        self.handler = ForgotResellerPasswordCommandHandler(repo=self.repo)

    @patch("core.tasks.reseller_emails.send_reseller_password_reset_email")
    def test_forgot_password_success(self, mock_email):
        reseller = _make_reseller()
        self.repo.find_by_email.return_value = reseller

        self.handler.handle(ForgotResellerPasswordCommand(email="partner@example.com"))

        self.repo.save.assert_called_once()
        assert reseller.reset_token is not None
        assert reseller.reset_token_expires_at is not None
        mock_email.delay.assert_called_once()

    @patch("core.tasks.reseller_emails.send_reseller_password_reset_email")
    def test_forgot_password_unknown_email_no_error(self, mock_email):
        self.repo.find_by_email.return_value = None

        # Should not raise
        self.handler.handle(ForgotResellerPasswordCommand(email="unknown@example.com"))

        self.repo.save.assert_not_called()
        mock_email.delay.assert_not_called()

    @patch("core.tasks.reseller_emails.send_reseller_password_reset_email")
    def test_forgot_password_oauth_only_no_email(self, mock_email):
        reseller = _make_reseller(password_hash=None)
        self.repo.find_by_email.return_value = reseller

        self.handler.handle(ForgotResellerPasswordCommand(email="partner@example.com"))

        self.repo.save.assert_not_called()
        mock_email.delay.assert_not_called()
