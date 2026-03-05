from unittest.mock import MagicMock

from src.reseller_bc.commission.application.queries.get_available_balance import (
    GetAvailableBalanceQuery,
    GetAvailableBalanceQueryHandler,
)


class TestGetAvailableBalanceQueryHandler:
    def setup_method(self):
        self.commission_repo = MagicMock()
        self.handler = GetAvailableBalanceQueryHandler(
            commission_repo=self.commission_repo,
        )

    def test_returns_confirmed_minus_paid_plus_clawbacks(self):
        self.commission_repo.sum_confirmed_by_reseller_id.return_value = 5000
        self.commission_repo.sum_paid_by_reseller_id.return_value = 2000
        self.commission_repo.sum_clawbacks_by_reseller_id.return_value = -500

        result = self.handler.handle(GetAvailableBalanceQuery(reseller_id="res1"))

        # 5000 - 2000 + (-500) = 2500
        assert result == 2500

    def test_all_zeros_returns_zero(self):
        self.commission_repo.sum_confirmed_by_reseller_id.return_value = 0
        self.commission_repo.sum_paid_by_reseller_id.return_value = 0
        self.commission_repo.sum_clawbacks_by_reseller_id.return_value = 0

        result = self.handler.handle(GetAvailableBalanceQuery(reseller_id="res1"))

        assert result == 0
