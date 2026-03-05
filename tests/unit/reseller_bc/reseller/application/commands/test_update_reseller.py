from unittest.mock import MagicMock

import pytest

from src.reseller_bc.reseller.application.commands.update_reseller import (
    UpdateResellerCommand,
    UpdateResellerCommandHandler,
)
from src.reseller_bc.reseller.domain.entities import Reseller
from src.reseller_bc.reseller.domain.enums import ResellerStatus
from src.reseller_bc.reseller.domain.exceptions import ResellerNotFoundException


class TestUpdateResellerCommandHandler:
    def setup_method(self):
        self.repo = MagicMock()
        self.handler = UpdateResellerCommandHandler(repo=self.repo)

    def _make_reseller(self) -> Reseller:
        return Reseller(
            id="reseller-123",
            email="test@example.com",
            name="Test",
            commission_pct=20,
            min_payout_cents=5000,
            referral_code="abc12345",
            status=ResellerStatus.ACTIVE,
        )

    def test_update_settings_success(self):
        reseller = self._make_reseller()
        self.repo.get_by_id.return_value = reseller

        self.handler.handle(UpdateResellerCommand(
            reseller_id="reseller-123",
            commission_pct=30,
            min_payout_cents=10000,
        ))

        self.repo.save.assert_called_once()
        assert reseller.commission_pct == 30
        assert reseller.min_payout_cents == 10000

    def test_update_status(self):
        reseller = self._make_reseller()
        self.repo.get_by_id.return_value = reseller

        self.handler.handle(UpdateResellerCommand(
            reseller_id="reseller-123",
            status="suspended",
        ))

        assert reseller.status == ResellerStatus.SUSPENDED

    def test_update_not_found(self):
        self.repo.get_by_id.return_value = None

        with pytest.raises(ResellerNotFoundException):
            self.handler.handle(UpdateResellerCommand(
                reseller_id="nonexistent",
                commission_pct=30,
            ))
