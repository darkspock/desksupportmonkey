from unittest.mock import MagicMock, patch

import pytest

from src.reseller_bc.reseller.application.commands.approve_reseller import (
    ApproveResellerCommand,
    ApproveResellerCommandHandler,
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


class TestApproveResellerCommandHandler:
    def setup_method(self):
        self.repo = MagicMock()
        self.handler = ApproveResellerCommandHandler(repo=self.repo)

    @patch("core.tasks.reseller_emails.send_reseller_approval_email")
    def test_approve_success(self, mock_email):
        reseller = _make_reseller()
        self.repo.get_by_id.return_value = reseller
        self.repo.exists_by_referral_code.return_value = False

        self.handler.handle(ApproveResellerCommand(reseller_id="res-1"))

        self.repo.save.assert_called_once()
        assert reseller.status == ResellerStatus.ACTIVE
        mock_email.delay.assert_called_once()

    def test_approve_not_found(self):
        self.repo.get_by_id.return_value = None

        with pytest.raises(ResellerNotFoundException):
            self.handler.handle(ApproveResellerCommand(reseller_id="nonexistent"))

    def test_approve_not_pending(self):
        reseller = _make_reseller(status=ResellerStatus.ACTIVE)
        self.repo.get_by_id.return_value = reseller

        with pytest.raises(ResellerPendingApprovalException):
            self.handler.handle(ApproveResellerCommand(reseller_id="res-1"))

        self.repo.save.assert_not_called()
