import pytest

from src.request_bc.request.domain.enums import (
    DEFAULT_PRIORITY,
    InvalidStatusTransitionError,
    PRIORITY_SORT_ORDER,
    RequestPriority,
    RequestStatus,
    RequestType,
    VALID_STATUS_TRANSITIONS,
)


class TestRequestStatusTransitions:
    def test_submitted_can_go_to_in_review(self):
        assert RequestStatus.IN_REVIEW in VALID_STATUS_TRANSITIONS[RequestStatus.SUBMITTED]

    def test_submitted_cannot_go_to_in_progress(self):
        assert RequestStatus.IN_PROGRESS not in VALID_STATUS_TRANSITIONS[RequestStatus.SUBMITTED]

    def test_in_review_can_go_to_in_progress(self):
        assert RequestStatus.IN_PROGRESS in VALID_STATUS_TRANSITIONS[RequestStatus.IN_REVIEW]

    def test_in_review_can_go_to_rejected(self):
        assert RequestStatus.REJECTED in VALID_STATUS_TRANSITIONS[RequestStatus.IN_REVIEW]

    def test_in_progress_can_go_to_resolved(self):
        assert RequestStatus.RESOLVED in VALID_STATUS_TRANSITIONS[RequestStatus.IN_PROGRESS]

    def test_in_progress_can_go_back_to_in_review(self):
        assert RequestStatus.IN_REVIEW in VALID_STATUS_TRANSITIONS[RequestStatus.IN_PROGRESS]

    def test_resolved_is_terminal(self):
        assert VALID_STATUS_TRANSITIONS[RequestStatus.RESOLVED] == []

    def test_rejected_is_terminal(self):
        assert VALID_STATUS_TRANSITIONS[RequestStatus.REJECTED] == []


class TestDefaultPriority:
    def test_incident_is_high(self):
        assert DEFAULT_PRIORITY[RequestType.INCIDENT] == RequestPriority.HIGH

    def test_new_equipment_is_low(self):
        assert DEFAULT_PRIORITY[RequestType.NEW_EQUIPMENT] == RequestPriority.LOW

    def test_onboarding_is_medium(self):
        assert DEFAULT_PRIORITY[RequestType.ONBOARDING] == RequestPriority.MEDIUM


class TestPrioritySortOrder:
    def test_urgent_is_highest(self):
        assert PRIORITY_SORT_ORDER[RequestPriority.URGENT] == 4

    def test_low_is_lowest(self):
        assert PRIORITY_SORT_ORDER[RequestPriority.LOW] == 1

    def test_order_is_correct(self):
        assert (
            PRIORITY_SORT_ORDER[RequestPriority.LOW]
            < PRIORITY_SORT_ORDER[RequestPriority.MEDIUM]
            < PRIORITY_SORT_ORDER[RequestPriority.HIGH]
            < PRIORITY_SORT_ORDER[RequestPriority.URGENT]
        )


class TestInvalidStatusTransitionError:
    def test_error_message(self):
        error = InvalidStatusTransitionError(RequestStatus.SUBMITTED, RequestStatus.RESOLVED)
        assert "submitted" in str(error)
        assert "resolved" in str(error)
        assert error.current == RequestStatus.SUBMITTED
        assert error.target == RequestStatus.RESOLVED
