"""Unit tests for CreateReferralAttributionCommandHandler."""
from unittest.mock import MagicMock

from src.reseller_bc.client.application.commands.create_referral_attribution import (
    CreateReferralAttributionCommand,
    CreateReferralAttributionCommandHandler,
)
from src.reseller_bc.client.domain.entities import ResellerClient
from src.reseller_bc.client.domain.enums import ClientSource
from src.reseller_bc.reseller.domain.entities import Reseller
from src.reseller_bc.reseller.domain.enums import ResellerStatus


def _make_reseller(status: ResellerStatus = ResellerStatus.ACTIVE) -> Reseller:
    r = Reseller.create(
        email="test@reseller.com",
        name="Test Reseller",
        commission_pct=20,
        min_payout_cents=5000,
    )
    if status == ResellerStatus.SUSPENDED:
        r.suspend()
    elif status == ResellerStatus.DEACTIVATED:
        r.deactivate()
    return r


class TestCreateReferralAttribution:
    def setup_method(self):
        self.reseller_repo = MagicMock()
        self.client_repo = MagicMock()
        self.handler = CreateReferralAttributionCommandHandler(
            reseller_repo=self.reseller_repo,
            client_repo=self.client_repo,
        )

    def test_valid_referral_creates_client(self):
        reseller = _make_reseller()
        self.reseller_repo.find_by_referral_code.return_value = reseller
        self.client_repo.find_by_company_id.return_value = None

        self.handler.handle(CreateReferralAttributionCommand(
            referral_code=reseller.referral_code,
            company_id="company-123",
        ))

        self.client_repo.save.assert_called_once()
        saved_client = self.client_repo.save.call_args[0][0]
        assert isinstance(saved_client, ResellerClient)
        assert saved_client.source == ClientSource.REFERRAL
        assert saved_client.is_demo is False
        assert saved_client.reseller_id == reseller.id
        assert saved_client.company_id == "company-123"

    def test_invalid_code_no_op(self):
        self.reseller_repo.find_by_referral_code.return_value = None

        self.handler.handle(CreateReferralAttributionCommand(
            referral_code="nonexistent",
            company_id="company-123",
        ))

        self.client_repo.save.assert_not_called()

    def test_suspended_reseller_no_op(self):
        reseller = _make_reseller(status=ResellerStatus.SUSPENDED)
        self.reseller_repo.find_by_referral_code.return_value = reseller

        self.handler.handle(CreateReferralAttributionCommand(
            referral_code=reseller.referral_code,
            company_id="company-123",
        ))

        self.client_repo.save.assert_not_called()

    def test_deactivated_reseller_no_op(self):
        reseller = _make_reseller(status=ResellerStatus.DEACTIVATED)
        self.reseller_repo.find_by_referral_code.return_value = reseller

        self.handler.handle(CreateReferralAttributionCommand(
            referral_code=reseller.referral_code,
            company_id="company-123",
        ))

        self.client_repo.save.assert_not_called()

    def test_already_attributed_company_no_op(self):
        reseller = _make_reseller()
        self.reseller_repo.find_by_referral_code.return_value = reseller
        self.client_repo.find_by_company_id.return_value = MagicMock()  # existing client

        self.handler.handle(CreateReferralAttributionCommand(
            referral_code=reseller.referral_code,
            company_id="company-123",
        ))

        self.client_repo.save.assert_not_called()
