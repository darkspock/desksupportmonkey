from unittest.mock import MagicMock, patch

import pytest

from src.reseller_bc.reseller.application.commands.reject_reseller import (
    RejectResellerCommand,
    RejectResellerCommandHandler,
)
from src.reseller_bc.reseller.domain.entities import Reseller
from src.reseller_bc.reseller.domain.enums import ResellerStatus
from src.reseller_bc.reseller.domain.exceptions import (
    ResellerNotFoundException,
    ResellerPendingApprovalException,
)


def _make_reseller(status=ResellerStatus.PENDING, **kwargs):
    return Reseller(
        id="res-1",
        email="partner@example.com",
        name="Partner Inc",
        commission_pct=20,
        min_payout_cents=5000,
        referral_code="abc12345",
        status=status,
        **kwargs,
    )


class TestRejectResellerCommandHandler:
    def setup_method(self):
        self.repo = MagicMock()
        self.handler = RejectResellerCommandHandler(repo=self.repo)

    @patch("core.tasks.reseller_emails.send_reseller_rejection_email")
    def test_reject_success(self, mock_email):
        reseller = _make_reseller()
        self.repo.get_by_id.return_value = reseller

        self.handler.handle(RejectResellerCommand(reseller_id="res-1", reason="Not suitable"))

        self.repo.save.assert_called_once()
        assert reseller.status == ResellerStatus.DEACTIVATED
        mock_email.delay.assert_called_once_with(
            to_email="partner@example.com",
            name="Partner Inc",
            reason="Not suitable",
        )

    @patch("core.tasks.reseller_emails.send_reseller_rejection_email")
    def test_reject_without_reason(self, mock_email):
        reseller = _make_reseller()
        self.repo.get_by_id.return_value = reseller

        self.handler.handle(RejectResellerCommand(reseller_id="res-1"))

        self.repo.save.assert_called_once()
        mock_email.delay.assert_called_once()

    def test_reject_not_found(self):
        self.repo.get_by_id.return_value = None

        with pytest.raises(ResellerNotFoundException):
            self.handler.handle(RejectResellerCommand(reseller_id="nonexistent"))

    def test_reject_not_pending(self):
        reseller = _make_reseller(status=ResellerStatus.ACTIVE)
        self.repo.get_by_id.return_value = reseller

        with pytest.raises(ResellerPendingApprovalException):
            self.handler.handle(RejectResellerCommand(reseller_id="res-1"))

        self.repo.save.assert_not_called()
