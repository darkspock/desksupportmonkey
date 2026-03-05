from unittest.mock import MagicMock

from src.reseller_bc.commission.application.commands.clawback_commission import (
    ClawbackCommissionCommand,
    ClawbackCommissionCommandHandler,
)
from src.reseller_bc.commission.domain.enums import CommissionStatus


class TestClawbackCommissionCommandHandler:
    def setup_method(self):
        self.commission_repo = MagicMock()
        self.handler = ClawbackCommissionCommandHandler(
            commission_repo=self.commission_repo,
        )

    def _make_command(self, **kwargs):
        defaults = {"stripe_invoice_id": "inv_123"}
        defaults.update(kwargs)
        return ClawbackCommissionCommand(**defaults)

    def _make_commission(self, status=CommissionStatus.PENDING):
        commission = MagicMock()
        commission.status = status
        commission.reseller_id = "res1"
        commission.reseller_client_id = "rc1"
        commission.company_id = "co1"
        commission.payment_amount_cents = 10000
        commission.commission_pct = 20
        commission.commission_amount_cents = 2000
        commission.stripe_invoice_id = "inv_123"
        commission.period_start = None
        commission.period_end = None
        return commission

    def test_pending_commission_clawback(self):
        commission = self._make_commission(CommissionStatus.PENDING)
        self.commission_repo.find_by_stripe_invoice_id.return_value = commission

        self.handler.handle(self._make_command())

        commission.clawback.assert_called_once()
        self.commission_repo.save.assert_called_once()

    def test_confirmed_commission_clawback(self):
        commission = self._make_commission(CommissionStatus.CONFIRMED)
        self.commission_repo.find_by_stripe_invoice_id.return_value = commission

        self.handler.handle(self._make_command())

        commission.clawback.assert_called_once()
        self.commission_repo.save.assert_called_once()

    def test_paid_commission_creates_negative_record(self):
        commission = self._make_commission(CommissionStatus.PAID)
        self.commission_repo.find_by_stripe_invoice_id.return_value = commission

        self.handler.handle(self._make_command())

        # save called twice: once for negative record, once for original clawback
        assert self.commission_repo.save.call_count == 2
        commission.clawback.assert_called_once()

    def test_already_clawed_back_skips(self):
        commission = self._make_commission(CommissionStatus.CLAWED_BACK)
        self.commission_repo.find_by_stripe_invoice_id.return_value = commission

        self.handler.handle(self._make_command())

        self.commission_repo.save.assert_not_called()

    def test_no_commission_found_skips(self):
        self.commission_repo.find_by_stripe_invoice_id.return_value = None

        self.handler.handle(self._make_command())

        self.commission_repo.save.assert_not_called()
