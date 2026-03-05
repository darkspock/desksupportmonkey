from unittest.mock import MagicMock

from src.reseller_bc.commission.application.commands.create_commission import (
    CreateCommissionCommand,
    CreateCommissionCommandHandler,
)
from src.reseller_bc.commission.domain.enums import CommissionStatus


class TestCreateCommissionCommandHandler:
    def setup_method(self):
        self.commission_repo = MagicMock()
        self.client_repo = MagicMock()
        self.reseller_repo = MagicMock()
        self.handler = CreateCommissionCommandHandler(
            commission_repo=self.commission_repo,
            client_repo=self.client_repo,
            reseller_repo=self.reseller_repo,
        )

    def _make_command(self, **kwargs):
        defaults = {
            "stripe_invoice_id": "inv_123",
            "company_id": "co1",
            "payment_amount_cents": 10000,
        }
        defaults.update(kwargs)
        return CreateCommissionCommand(**defaults)

    def test_valid_commission_created(self):
        client = MagicMock(is_demo=False, reseller_id="res1", id="rc1")
        reseller = MagicMock(id="res1", commission_pct=20)
        self.client_repo.find_by_company_id.return_value = client
        self.commission_repo.find_by_stripe_invoice_id.return_value = None
        self.reseller_repo.get_by_id.return_value = reseller

        self.handler.handle(self._make_command())

        self.commission_repo.save.assert_called_once()
        saved = self.commission_repo.save.call_args[0][0]
        assert saved.commission_amount_cents == 2000
        assert saved.status == CommissionStatus.PENDING

    def test_no_reseller_client_skips(self):
        self.client_repo.find_by_company_id.return_value = None

        self.handler.handle(self._make_command())

        self.commission_repo.save.assert_not_called()

    def test_demo_account_skips(self):
        client = MagicMock(is_demo=True)
        self.client_repo.find_by_company_id.return_value = client

        self.handler.handle(self._make_command())

        self.commission_repo.save.assert_not_called()

    def test_already_processed_skips(self):
        client = MagicMock(is_demo=False, reseller_id="res1")
        self.client_repo.find_by_company_id.return_value = client
        self.commission_repo.find_by_stripe_invoice_id.return_value = MagicMock()

        self.handler.handle(self._make_command())

        self.commission_repo.save.assert_not_called()

    def test_orphaned_client_skips(self):
        client = MagicMock(is_demo=False, reseller_id="res1")
        self.client_repo.find_by_company_id.return_value = client
        self.commission_repo.find_by_stripe_invoice_id.return_value = None
        self.reseller_repo.get_by_id.return_value = None

        self.handler.handle(self._make_command())

        self.commission_repo.save.assert_not_called()
