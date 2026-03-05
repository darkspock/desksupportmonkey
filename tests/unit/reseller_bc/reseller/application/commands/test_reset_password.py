from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from src.reseller_bc.reseller.application.commands.reset_password import (
    ResetResellerPasswordCommand,
    ResetResellerPasswordCommandHandler,
)
from src.reseller_bc.reseller.domain.entities import Reseller
from src.reseller_bc.reseller.domain.enums import ResellerStatus
from src.reseller_bc.reseller.domain.exceptions import (
    ResellerInvalidPasswordException,
    ResellerInvalidResetTokenException,
)


def _make_reseller(
    token="valid-token",
    expires_at=None,
    password_hash="hashed",
):
    return Reseller(
        id="res-1",
        email="partner@example.com",
        name="Partner Inc",
        commission_pct=20,
        min_payout_cents=5000,
        referral_code="abc12345",
        status=ResellerStatus.ACTIVE,
        password_hash=password_hash,
        reset_token=token,
        reset_token_expires_at=expires_at or datetime.now(timezone.utc) + timedelta(hours=1),
    )


class TestResetResellerPasswordCommandHandler:
    def setup_method(self):
        self.repo = MagicMock()
        self.password_service = MagicMock()
        self.password_service.hash_password.return_value = "new_hashed"
        self.handler = ResetResellerPasswordCommandHandler(
            repo=self.repo, password_service=self.password_service,
        )

    def test_reset_success(self):
        reseller = _make_reseller()
        self.repo.find_by_reset_token.return_value = reseller

        self.handler.handle(ResetResellerPasswordCommand(
            token="valid-token", new_password="newpass1234",
        ))

        self.repo.save.assert_called_once()
        assert reseller.password_hash == "new_hashed"
        assert reseller.reset_token is None
        assert reseller.reset_token_expires_at is None

    def test_reset_invalid_token(self):
        self.repo.find_by_reset_token.return_value = None

        with pytest.raises(ResellerInvalidResetTokenException):
            self.handler.handle(ResetResellerPasswordCommand(
                token="bad-token", new_password="newpass1234",
            ))

    def test_reset_expired_token(self):
        reseller = _make_reseller(
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        self.repo.find_by_reset_token.return_value = reseller

        with pytest.raises(ResellerInvalidResetTokenException, match="expired"):
            self.handler.handle(ResetResellerPasswordCommand(
                token="valid-token", new_password="newpass1234",
            ))

    def test_reset_short_password(self):
        reseller = _make_reseller()
        self.repo.find_by_reset_token.return_value = reseller

        with pytest.raises(ResellerInvalidPasswordException, match="at least 8"):
            self.handler.handle(ResetResellerPasswordCommand(
                token="valid-token", new_password="short",
            ))
