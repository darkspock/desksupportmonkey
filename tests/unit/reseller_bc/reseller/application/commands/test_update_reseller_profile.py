from unittest.mock import MagicMock

import pytest

from src.reseller_bc.reseller.application.commands.update_reseller_profile import (
    UpdateResellerProfileCommand,
    UpdateResellerProfileCommandHandler,
)
from src.reseller_bc.reseller.domain.entities import Reseller
from src.reseller_bc.reseller.domain.enums import ResellerStatus
from src.reseller_bc.reseller.domain.exceptions import ResellerNotFoundException


class TestUpdateResellerProfileCommandHandler:
    def setup_method(self):
        self.repo = MagicMock()
        self.handler = UpdateResellerProfileCommandHandler(repo=self.repo)

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

    def test_update_profile_success(self):
        reseller = self._make_reseller()
        self.repo.get_by_id.return_value = reseller

        self.handler.handle(UpdateResellerProfileCommand(
            reseller_id="reseller-123",
            company_name="Acme Corp",
            tax_id="123-456",
        ))

        self.repo.save.assert_called_once()
        assert reseller.company_name == "Acme Corp"
        assert reseller.tax_id == "123-456"

    def test_update_profile_not_found(self):
        self.repo.get_by_id.return_value = None

        with pytest.raises(ResellerNotFoundException):
            self.handler.handle(UpdateResellerProfileCommand(
                reseller_id="nonexistent",
                company_name="Test",
            ))
