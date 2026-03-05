from unittest.mock import MagicMock

import pytest

from src.reseller_bc.payout.application.commands.process_payout import (
    ProcessPayoutCommand,
    ProcessPayoutCommandHandler,
)
from src.reseller_bc.payout.domain.entities import ResellerPayout
from src.reseller_bc.payout.domain.enums import PayoutStatus
from src.reseller_bc.payout.domain.exceptions import (
    InvalidPayoutTransitionException,
    PayoutNotFoundException,
)


def _make_payout(status=PayoutStatus.REQUESTED):
    payout = ResellerPayout.create(reseller_id="r1", amount_cents=10000, id="p1")
    if status == PayoutStatus.APPROVED:
        payout.approve(processed_by="admin0")
    elif status == PayoutStatus.REJECTED:
        payout.reject(processed_by="admin0")
    elif status == PayoutStatus.PAID:
        payout.approve(processed_by="admin0")
        payout.mark_paid(payment_reference="REF")
    return payout


def _make_handler(payout=None):
    payout_repo = MagicMock()
    commission_repo = MagicMock()
    payout_repo.find_by_id.return_value = payout
    handler = ProcessPayoutCommandHandler(payout_repo, commission_repo)
    return handler, payout_repo, commission_repo


class TestProcessPayoutCommandHandler:
    def test_approve_payout(self):
        payout = _make_payout(PayoutStatus.REQUESTED)
        handler, payout_repo, _ = _make_handler(payout)
        handler.handle(ProcessPayoutCommand(
            payout_id="p1", action="approve", processed_by="admin1",
        ))
        assert payout.status == PayoutStatus.APPROVED
        payout_repo.save.assert_called_once()

    def test_reject_payout_with_notes(self):
        payout = _make_payout(PayoutStatus.REQUESTED)
        handler, payout_repo, _ = _make_handler(payout)
        handler.handle(ProcessPayoutCommand(
            payout_id="p1", action="reject", processed_by="admin1",
            notes="Incomplete documentation",
        ))
        assert payout.status == PayoutStatus.REJECTED
        assert payout.notes == "Incomplete documentation"
        payout_repo.save.assert_called_once()

    def test_mark_paid_transitions_commissions(self):
        payout = _make_payout(PayoutStatus.APPROVED)
        handler, payout_repo, commission_repo = _make_handler(payout)
        handler.handle(ProcessPayoutCommand(
            payout_id="p1", action="mark_paid", processed_by="admin1",
            payment_reference="WIRE-2026-001",
        ))
        assert payout.status == PayoutStatus.PAID
        assert payout.payment_reference == "WIRE-2026-001"
        commission_repo.mark_confirmed_as_paid_for_reseller.assert_called_once_with("r1")
        payout_repo.save.assert_called_once()

    def test_mark_paid_without_reference_raises(self):
        payout = _make_payout(PayoutStatus.APPROVED)
        handler, _, _ = _make_handler(payout)
        with pytest.raises(ValueError, match="payment_reference"):
            handler.handle(ProcessPayoutCommand(
                payout_id="p1", action="mark_paid", processed_by="admin1",
            ))

    def test_process_payout_not_found(self):
        handler, _, _ = _make_handler(payout=None)
        with pytest.raises(PayoutNotFoundException):
            handler.handle(ProcessPayoutCommand(
                payout_id="p1", action="approve", processed_by="admin1",
            ))

    def test_invalid_action_raises(self):
        payout = _make_payout(PayoutStatus.REQUESTED)
        handler, _, _ = _make_handler(payout)
        with pytest.raises(ValueError, match="Unknown action"):
            handler.handle(ProcessPayoutCommand(
                payout_id="p1", action="cancel", processed_by="admin1",
            ))

    def test_approve_already_approved_raises(self):
        payout = _make_payout(PayoutStatus.APPROVED)
        handler, _, _ = _make_handler(payout)
        with pytest.raises(InvalidPayoutTransitionException):
            handler.handle(ProcessPayoutCommand(
                payout_id="p1", action="approve", processed_by="admin1",
            ))
