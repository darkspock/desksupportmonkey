from unittest.mock import MagicMock

import pytest

from src.reseller_bc.reseller.application.commands.change_password import (
    ChangeResellerPasswordCommand,
    ChangeResellerPasswordCommandHandler,
)
from src.reseller_bc.reseller.domain.entities import Reseller
from src.reseller_bc.reseller.domain.enums import ResellerStatus
from src.reseller_bc.reseller.domain.exceptions import (
    ResellerInvalidPasswordException,
    ResellerNotFoundException,
)


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


class TestChangeResellerPasswordCommandHandler:
    def setup_method(self):
        self.repo = MagicMock()
        self.password_service = MagicMock()
        self.password_service.hash_password.return_value = "new_hashed"
        self.handler = ChangeResellerPasswordCommandHandler(
            repo=self.repo, password_service=self.password_service,
        )

    def test_change_password_success(self):
        reseller = _make_reseller()
        self.repo.get_by_id.return_value = reseller
        self.password_service.verify_password.return_value = True

        self.handler.handle(ChangeResellerPasswordCommand(
            reseller_id="res-1",
            current_password="oldpass123",
            new_password="newpass1234",
        ))

        self.repo.save.assert_called_once()
        assert reseller.password_hash == "new_hashed"

    def test_change_password_not_found(self):
        self.repo.get_by_id.return_value = None

        with pytest.raises(ResellerNotFoundException):
            self.handler.handle(ChangeResellerPasswordCommand(
                reseller_id="nonexistent",
                current_password="old",
                new_password="newpass1234",
            ))

    def test_change_password_wrong_current(self):
        reseller = _make_reseller()
        self.repo.get_by_id.return_value = reseller
        self.password_service.verify_password.return_value = False

        with pytest.raises(ResellerInvalidPasswordException, match="Current password"):
            self.handler.handle(ChangeResellerPasswordCommand(
                reseller_id="res-1",
                current_password="wrongpass",
                new_password="newpass1234",
            ))

        self.repo.save.assert_not_called()

    def test_change_password_too_short(self):
        reseller = _make_reseller()
        self.repo.get_by_id.return_value = reseller
        self.password_service.verify_password.return_value = True

        with pytest.raises(ResellerInvalidPasswordException, match="at least 8"):
            self.handler.handle(ChangeResellerPasswordCommand(
                reseller_id="res-1",
                current_password="oldpass123",
                new_password="short",
            ))

        self.repo.save.assert_not_called()

    def test_change_password_oauth_only(self):
        reseller = _make_reseller(password_hash=None)
        self.repo.get_by_id.return_value = reseller

        with pytest.raises(ResellerInvalidPasswordException, match="OAuth"):
            self.handler.handle(ChangeResellerPasswordCommand(
                reseller_id="res-1",
                current_password="anything",
                new_password="newpass1234",
            ))
