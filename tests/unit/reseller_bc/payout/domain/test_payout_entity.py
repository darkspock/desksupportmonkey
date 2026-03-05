import pytest

from src.reseller_bc.payout.domain.entities import ResellerPayout
from src.reseller_bc.payout.domain.enums import PayoutStatus
from src.reseller_bc.payout.domain.exceptions import (
    InvalidPayoutAmountException,
    InvalidPayoutTransitionException,
)


class TestResellerPayoutCreate:
    def test_create_payout_sets_requested_status(self):
        payout = ResellerPayout.create(reseller_id="r1", amount_cents=10000)
        assert payout.status == PayoutStatus.REQUESTED
        assert payout.amount_cents == 10000
        assert payout.reseller_id == "r1"
        assert payout.requested_at is not None
        assert payout.processed_at is None
        assert payout.processed_by is None
        assert payout.payment_reference is None
        assert payout.notes is None

    def test_create_payout_with_custom_id(self):
        payout = ResellerPayout.create(reseller_id="r1", amount_cents=5000, id="custom-id")
        assert payout.id == "custom-id"

    def test_create_payout_with_zero_amount_raises(self):
        with pytest.raises(InvalidPayoutAmountException):
            ResellerPayout.create(reseller_id="r1", amount_cents=0)

    def test_create_payout_with_negative_amount_raises(self):
        with pytest.raises(InvalidPayoutAmountException):
            ResellerPayout.create(reseller_id="r1", amount_cents=-100)


class TestResellerPayoutApprove:
    def test_approve_from_requested(self):
        payout = ResellerPayout.create(reseller_id="r1", amount_cents=10000)
        payout.approve(processed_by="admin1")
        assert payout.status == PayoutStatus.APPROVED
        assert payout.processed_by == "admin1"
        assert payout.processed_at is not None

    def test_approve_from_approved_raises(self):
        payout = ResellerPayout.create(reseller_id="r1", amount_cents=10000)
        payout.approve(processed_by="admin1")
        with pytest.raises(InvalidPayoutTransitionException):
            payout.approve(processed_by="admin2")

    def test_approve_from_rejected_raises(self):
        payout = ResellerPayout.create(reseller_id="r1", amount_cents=10000)
        payout.reject(processed_by="admin1")
        with pytest.raises(InvalidPayoutTransitionException):
            payout.approve(processed_by="admin2")

    def test_approve_from_paid_raises(self):
        payout = ResellerPayout.create(reseller_id="r1", amount_cents=10000)
        payout.approve(processed_by="admin1")
        payout.mark_paid(payment_reference="REF-001")
        with pytest.raises(InvalidPayoutTransitionException):
            payout.approve(processed_by="admin2")


class TestResellerPayoutReject:
    def test_reject_from_requested(self):
        payout = ResellerPayout.create(reseller_id="r1", amount_cents=10000)
        payout.reject(processed_by="admin1", notes="Incomplete tax info")
        assert payout.status == PayoutStatus.REJECTED
        assert payout.processed_by == "admin1"
        assert payout.processed_at is not None
        assert payout.notes == "Incomplete tax info"

    def test_reject_from_requested_without_notes(self):
        payout = ResellerPayout.create(reseller_id="r1", amount_cents=10000)
        payout.reject(processed_by="admin1")
        assert payout.status == PayoutStatus.REJECTED
        assert payout.notes is None

    def test_reject_from_approved_raises(self):
        payout = ResellerPayout.create(reseller_id="r1", amount_cents=10000)
        payout.approve(processed_by="admin1")
        with pytest.raises(InvalidPayoutTransitionException):
            payout.reject(processed_by="admin2")


class TestResellerPayoutMarkPaid:
    def test_mark_paid_from_approved(self):
        payout = ResellerPayout.create(reseller_id="r1", amount_cents=10000)
        payout.approve(processed_by="admin1")
        payout.mark_paid(payment_reference="WIRE-2026-001")
        assert payout.status == PayoutStatus.PAID
        assert payout.payment_reference == "WIRE-2026-001"
        assert payout.processed_at is not None

    def test_mark_paid_from_requested_raises(self):
        payout = ResellerPayout.create(reseller_id="r1", amount_cents=10000)
        with pytest.raises(InvalidPayoutTransitionException):
            payout.mark_paid(payment_reference="REF-001")

    def test_mark_paid_from_rejected_raises(self):
        payout = ResellerPayout.create(reseller_id="r1", amount_cents=10000)
        payout.reject(processed_by="admin1")
        with pytest.raises(InvalidPayoutTransitionException):
            payout.mark_paid(payment_reference="REF-001")
