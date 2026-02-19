import pytest

from src.procurement_bc.purchase_order.domain.enums import (
    InvalidPOStatusTransitionError,
    PurchaseOrderStatus,
    VALID_TRANSITIONS,
)


class TestPurchaseOrderStatus:
    def test_all_statuses_in_valid_transitions(self):
        for status in PurchaseOrderStatus:
            assert status in VALID_TRANSITIONS

    def test_terminal_statuses(self):
        assert PurchaseOrderStatus.CLOSED.is_terminal is True
        assert (
            PurchaseOrderStatus.CANCELLED.is_terminal is True
        )

    def test_non_terminal_statuses(self):
        non_terminal = [
            PurchaseOrderStatus.DRAFT,
            PurchaseOrderStatus.SUBMITTED,
            PurchaseOrderStatus.APPROVED,
            PurchaseOrderStatus.ORDERED,
            PurchaseOrderStatus.PARTIALLY_RECEIVED,
            PurchaseOrderStatus.RECEIVED,
        ]
        for status in non_terminal:
            assert status.is_terminal is False

    def test_countable_for_budget(self):
        countable = [
            PurchaseOrderStatus.APPROVED,
            PurchaseOrderStatus.ORDERED,
            PurchaseOrderStatus.PARTIALLY_RECEIVED,
            PurchaseOrderStatus.RECEIVED,
            PurchaseOrderStatus.CLOSED,
        ]
        for status in countable:
            assert status.is_countable_for_budget is True

    def test_not_countable_for_budget(self):
        non_countable = [
            PurchaseOrderStatus.DRAFT,
            PurchaseOrderStatus.SUBMITTED,
            PurchaseOrderStatus.CANCELLED,
        ]
        for status in non_countable:
            assert status.is_countable_for_budget is False

    def test_terminal_statuses_have_no_transitions(self):
        assert VALID_TRANSITIONS[PurchaseOrderStatus.CLOSED] == []
        assert VALID_TRANSITIONS[PurchaseOrderStatus.CANCELLED] == []

    def test_invalid_po_status_transition_error(self):
        error = InvalidPOStatusTransitionError(
            PurchaseOrderStatus.CLOSED,
            PurchaseOrderStatus.DRAFT,
        )
        assert "CLOSED" in str(error)
        assert "DRAFT" in str(error)
