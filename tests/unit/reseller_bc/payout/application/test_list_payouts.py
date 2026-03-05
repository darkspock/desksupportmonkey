from unittest.mock import MagicMock

from src.reseller_bc.payout.application.queries.list_payouts import (
    ListPayoutsQuery,
    ListPayoutsQueryHandler,
)
from src.reseller_bc.payout.domain.entities import ResellerPayout
from src.reseller_bc.reseller.domain.entities import Reseller


def _make_reseller():
    return Reseller(
        id="r1",
        email="reseller@example.com",
        name="Test Reseller",
    )


def _make_payout():
    return ResellerPayout.create(reseller_id="r1", amount_cents=10000, id="p1")


class TestListPayoutsQueryHandler:
    def test_list_payouts_by_reseller(self):
        payout = _make_payout()
        reseller = _make_reseller()

        payout_repo = MagicMock()
        reseller_repo = MagicMock()
        payout_repo.find_by_reseller_id.return_value = [payout]
        payout_repo.count_by_reseller_id.return_value = 1
        reseller_repo.get_by_id.return_value = reseller

        handler = ListPayoutsQueryHandler(payout_repo, reseller_repo)
        result = handler.handle(ListPayoutsQuery(reseller_id="r1", offset=0, limit=50))

        assert result.total == 1
        assert len(result.items) == 1
        assert result.items[0].id == "p1"
        assert result.items[0].reseller_name == "Test Reseller"
        payout_repo.find_by_reseller_id.assert_called_once_with("r1", 0, 50)

    def test_list_all_payouts(self):
        payout = _make_payout()
        reseller = _make_reseller()

        payout_repo = MagicMock()
        reseller_repo = MagicMock()
        payout_repo.find_all.return_value = [payout]
        payout_repo.count_all.return_value = 1
        reseller_repo.get_by_id.return_value = reseller

        handler = ListPayoutsQueryHandler(payout_repo, reseller_repo)
        result = handler.handle(ListPayoutsQuery(offset=0, limit=50))

        assert result.total == 1
        assert len(result.items) == 1
        payout_repo.find_all.assert_called_once_with(0, 50)

    def test_list_payouts_empty(self):
        payout_repo = MagicMock()
        reseller_repo = MagicMock()
        payout_repo.find_by_reseller_id.return_value = []
        payout_repo.count_by_reseller_id.return_value = 0

        handler = ListPayoutsQueryHandler(payout_repo, reseller_repo)
        result = handler.handle(ListPayoutsQuery(reseller_id="r1"))

        assert result.total == 0
        assert len(result.items) == 0
