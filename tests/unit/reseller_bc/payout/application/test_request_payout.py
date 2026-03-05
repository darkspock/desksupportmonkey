from unittest.mock import MagicMock

import pytest

from src.reseller_bc.payout.application.commands.request_payout import (
    RequestPayoutCommand,
    RequestPayoutCommandHandler,
)
from src.reseller_bc.payout.domain.exceptions import (
    InsufficientBalanceException,
    PayoutAlreadyPendingException,
)
from src.reseller_bc.reseller.domain.entities import Reseller
from src.reseller_bc.reseller.domain.enums import ResellerStatus
from src.reseller_bc.reseller.domain.exceptions import (
    ResellerNotFoundException,
    ResellerSuspendedException,
)


def _make_reseller(status=ResellerStatus.ACTIVE, min_payout_cents=5000):
    return Reseller(
        id="r1",
        email="reseller@example.com",
        name="Test Reseller",
        min_payout_cents=min_payout_cents,
        status=status,
    )


def _make_handler(reseller=None, active_payout=None, confirmed=0, paid=0, clawbacks=0):
    payout_repo = MagicMock()
    commission_repo = MagicMock()
    reseller_repo = MagicMock()

    reseller_repo.get_by_id.return_value = reseller
    payout_repo.find_active_by_reseller_id.return_value = active_payout
    commission_repo.sum_confirmed_by_reseller_id.return_value = confirmed
    commission_repo.sum_paid_by_reseller_id.return_value = paid
    commission_repo.sum_clawbacks_by_reseller_id.return_value = clawbacks

    handler = RequestPayoutCommandHandler(payout_repo, commission_repo, reseller_repo)
    return handler, payout_repo


class TestRequestPayoutCommandHandler:
    def test_request_payout_success(self):
        reseller = _make_reseller(min_payout_cents=5000)
        handler, payout_repo = _make_handler(
            reseller=reseller, confirmed=10000, paid=0, clawbacks=0,
        )
        handler.handle(RequestPayoutCommand(id="p1", reseller_id="r1"))
        payout_repo.save.assert_called_once()
        saved = payout_repo.save.call_args[0][0]
        assert saved.amount_cents == 10000
        assert saved.reseller_id == "r1"

    def test_request_payout_reseller_not_found(self):
        handler, _ = _make_handler(reseller=None)
        with pytest.raises(ResellerNotFoundException):
            handler.handle(RequestPayoutCommand(id="p1", reseller_id="r1"))

    def test_request_payout_reseller_suspended(self):
        reseller = _make_reseller(status=ResellerStatus.SUSPENDED)
        handler, _ = _make_handler(reseller=reseller)
        with pytest.raises(ResellerSuspendedException):
            handler.handle(RequestPayoutCommand(id="p1", reseller_id="r1"))

    def test_request_payout_already_pending(self):
        reseller = _make_reseller()
        active = MagicMock()
        handler, _ = _make_handler(reseller=reseller, active_payout=active)
        with pytest.raises(PayoutAlreadyPendingException):
            handler.handle(RequestPayoutCommand(id="p1", reseller_id="r1"))

    def test_request_payout_insufficient_balance(self):
        reseller = _make_reseller(min_payout_cents=5000)
        handler, _ = _make_handler(
            reseller=reseller, confirmed=3000, paid=0, clawbacks=0,
        )
        with pytest.raises(InsufficientBalanceException):
            handler.handle(RequestPayoutCommand(id="p1", reseller_id="r1"))

    def test_request_payout_balance_with_clawbacks(self):
        reseller = _make_reseller(min_payout_cents=5000)
        handler, payout_repo = _make_handler(
            reseller=reseller, confirmed=10000, paid=2000, clawbacks=-1000,
        )
        handler.handle(RequestPayoutCommand(id="p1", reseller_id="r1"))
        payout_repo.save.assert_called_once()
        saved = payout_repo.save.call_args[0][0]
        assert saved.amount_cents == 7000  # 10000 - 2000 + (-1000)
