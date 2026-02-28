import pytest

from src.change_bc.change_request.domain.enums import (
    ChangeEventType,
    ChangeStatus,
    ChangeType,
    InvalidStatusTransitionError,
    PIROutcome,
    VALID_TRANSITIONS,
)


class TestChangeType:
    def test_values(self):
        assert ChangeType.STANDARD == "standard"
        assert ChangeType.NORMAL == "normal"
        assert ChangeType.EMERGENCY == "emergency"

    def test_count(self):
        assert len(ChangeType) == 3


class TestChangeStatus:
    def test_values(self):
        assert ChangeStatus.DRAFT == "draft"
        assert ChangeStatus.PENDING_APPROVAL == "pending_approval"
        assert ChangeStatus.SCHEDULED == "scheduled"
        assert ChangeStatus.IN_PROGRESS == "in_progress"
        assert ChangeStatus.IMPLEMENTED == "implemented"
        assert ChangeStatus.CLOSED == "closed"
        assert ChangeStatus.REJECTED == "rejected"
        assert ChangeStatus.ROLLED_BACK == "rolled_back"

    def test_count(self):
        assert len(ChangeStatus) == 8

    def test_is_terminal_closed(self):
        assert ChangeStatus.CLOSED.is_terminal is True

    def test_is_terminal_rejected(self):
        assert ChangeStatus.REJECTED.is_terminal is True

    def test_is_terminal_rolled_back(self):
        assert ChangeStatus.ROLLED_BACK.is_terminal is True

    def test_is_terminal_non_terminal(self):
        non_terminal = [
            ChangeStatus.DRAFT,
            ChangeStatus.PENDING_APPROVAL,
            ChangeStatus.SCHEDULED,
            ChangeStatus.IN_PROGRESS,
            ChangeStatus.IMPLEMENTED,
        ]
        for s in non_terminal:
            assert s.is_terminal is False, f"{s} should not be terminal"


class TestValidTransitions:
    def test_covers_all_statuses(self):
        for status in ChangeStatus:
            assert status in VALID_TRANSITIONS

    def test_draft_transitions(self):
        targets = VALID_TRANSITIONS[ChangeStatus.DRAFT]
        assert ChangeStatus.PENDING_APPROVAL in targets
        assert ChangeStatus.SCHEDULED in targets

    def test_pending_approval_transitions(self):
        targets = VALID_TRANSITIONS[ChangeStatus.PENDING_APPROVAL]
        assert ChangeStatus.SCHEDULED in targets
        assert ChangeStatus.REJECTED in targets

    def test_terminal_states_have_no_transitions(self):
        for status in [
            ChangeStatus.CLOSED,
            ChangeStatus.REJECTED,
            ChangeStatus.ROLLED_BACK,
        ]:
            assert VALID_TRANSITIONS[status] == []


class TestChangeEventType:
    def test_count(self):
        assert len(ChangeEventType) == 13

    def test_values(self):
        assert ChangeEventType.CREATED == "created"
        assert ChangeEventType.SUBMITTED == "submitted"
        assert ChangeEventType.APPROVED == "approved"
        assert ChangeEventType.REJECTED == "rejected"
        assert ChangeEventType.ASSIGNED == "assigned"
        assert ChangeEventType.PIR_ADDED == "pir_added"


class TestPIROutcome:
    def test_values(self):
        assert PIROutcome.SUCCESSFUL == "successful"
        assert PIROutcome.PARTIAL == "partial"
        assert PIROutcome.FAILED == "failed"

    def test_count(self):
        assert len(PIROutcome) == 3


class TestInvalidStatusTransitionError:
    def test_stores_current_and_target(self):
        error = InvalidStatusTransitionError(
            ChangeStatus.DRAFT, ChangeStatus.CLOSED
        )
        assert error.current == ChangeStatus.DRAFT
        assert error.target == ChangeStatus.CLOSED
        assert "draft" in str(error)
        assert "closed" in str(error)
