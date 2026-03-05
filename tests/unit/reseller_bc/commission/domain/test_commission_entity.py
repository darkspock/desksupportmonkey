from src.reseller_bc.commission.domain.entities import ResellerCommission
from src.reseller_bc.commission.domain.enums import CommissionStatus


class TestResellerCommissionCreate:
    def test_create_calculates_commission_correctly(self):
        commission = ResellerCommission.create(
            reseller_id="res1",
            reseller_client_id="rc1",
            company_id="co1",
            payment_amount_cents=10000,
            commission_pct=20,
            stripe_invoice_id="inv_123",
        )
        assert commission.commission_amount_cents == 2000

    def test_create_sets_status_pending(self):
        commission = ResellerCommission.create(
            reseller_id="res1",
            reseller_client_id="rc1",
            company_id="co1",
            payment_amount_cents=10000,
            commission_pct=20,
            stripe_invoice_id="inv_123",
        )
        assert commission.status == CommissionStatus.PENDING

    def test_create_rounds_down(self):
        commission = ResellerCommission.create(
            reseller_id="res1",
            reseller_client_id="rc1",
            company_id="co1",
            payment_amount_cents=999,
            commission_pct=15,
            stripe_invoice_id="inv_123",
        )
        # 999 * 15 // 100 = 149 (not 150)
        assert commission.commission_amount_cents == 149


class TestResellerCommissionClawback:
    def test_create_clawback_produces_negative_amounts(self):
        original = ResellerCommission.create(
            reseller_id="res1",
            reseller_client_id="rc1",
            company_id="co1",
            payment_amount_cents=10000,
            commission_pct=20,
            stripe_invoice_id="inv_123",
        )
        clawback = ResellerCommission.create_clawback(original)
        assert clawback.payment_amount_cents == -10000
        assert clawback.commission_amount_cents == -2000

    def test_create_clawback_status_is_clawed_back(self):
        original = ResellerCommission.create(
            reseller_id="res1",
            reseller_client_id="rc1",
            company_id="co1",
            payment_amount_cents=10000,
            commission_pct=20,
            stripe_invoice_id="inv_123",
        )
        clawback = ResellerCommission.create_clawback(original)
        assert clawback.status == CommissionStatus.CLAWED_BACK


class TestResellerCommissionTransitions:
    def test_confirm_sets_confirmed(self):
        commission = ResellerCommission.create(
            reseller_id="res1",
            reseller_client_id="rc1",
            company_id="co1",
            payment_amount_cents=10000,
            commission_pct=20,
            stripe_invoice_id="inv_123",
        )
        commission.confirm()
        assert commission.status == CommissionStatus.CONFIRMED

    def test_clawback_sets_clawed_back(self):
        commission = ResellerCommission.create(
            reseller_id="res1",
            reseller_client_id="rc1",
            company_id="co1",
            payment_amount_cents=10000,
            commission_pct=20,
            stripe_invoice_id="inv_123",
        )
        commission.clawback()
        assert commission.status == CommissionStatus.CLAWED_BACK
