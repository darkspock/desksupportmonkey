"""Unit tests for waiting_for_employee status: transitions, SLA pause/resume, auto-transition."""
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, call

import pytest

from src.request_bc.request.domain.entities import RequestComment, RequestEvent, ServiceRequest
from src.request_bc.request.domain.enums import (
    InvalidStatusTransitionError,
    RequestPriority,
    RequestStatus,
    RequestType,
    VALID_STATUS_TRANSITIONS,
)
from src.request_bc.request.application.commands.add_comment import (
    AddCommentCommand,
    AddCommentCommandHandler,
)


# ── Helpers ──────────────────────────────────────────────────────

def _make_request(
    status: RequestStatus = RequestStatus.IN_PROGRESS,
    hours_ago: float = 4,
    sla_paused_at: datetime | None = None,
    sla_paused_total_seconds: int = 0,
) -> ServiceRequest:
    now = datetime.now(timezone.utc)
    return ServiceRequest(
        id="r1",
        company_id="c1",
        created_by="u_employee",
        type=RequestType.INCIDENT,
        title="Test",
        description="Test",
        status=status,
        priority=RequestPriority.HIGH,
        created_at=now - timedelta(hours=hours_ago),
        sla_paused_at=sla_paused_at,
        sla_paused_total_seconds=sla_paused_total_seconds,
    )


# ── Status Transitions ──────────────────────────────────────────

class TestWaitingForEmployeeTransitions:
    def test_in_progress_to_waiting_is_valid(self):
        req = _make_request(status=RequestStatus.IN_PROGRESS)
        req.change_status(RequestStatus.WAITING_FOR_EMPLOYEE)
        assert req.status == RequestStatus.WAITING_FOR_EMPLOYEE

    def test_waiting_to_in_progress_is_valid(self):
        req = _make_request(status=RequestStatus.WAITING_FOR_EMPLOYEE)
        req.change_status(RequestStatus.IN_PROGRESS)
        assert req.status == RequestStatus.IN_PROGRESS

    def test_waiting_to_resolved_is_valid(self):
        req = _make_request(status=RequestStatus.WAITING_FOR_EMPLOYEE)
        req.change_status(RequestStatus.RESOLVED)
        assert req.status == RequestStatus.RESOLVED
        assert req.resolved_at is not None

    def test_waiting_to_rejected_is_valid(self):
        req = _make_request(status=RequestStatus.WAITING_FOR_EMPLOYEE)
        req.change_status(RequestStatus.REJECTED)
        assert req.status == RequestStatus.REJECTED
        assert req.resolved_at is not None

    def test_submitted_to_waiting_is_invalid(self):
        req = _make_request(status=RequestStatus.SUBMITTED)
        with pytest.raises(InvalidStatusTransitionError):
            req.change_status(RequestStatus.WAITING_FOR_EMPLOYEE)

    def test_in_review_to_waiting_is_invalid(self):
        req = _make_request(status=RequestStatus.IN_REVIEW)
        with pytest.raises(InvalidStatusTransitionError):
            req.change_status(RequestStatus.WAITING_FOR_EMPLOYEE)

    def test_resolved_to_waiting_is_invalid(self):
        req = _make_request(status=RequestStatus.RESOLVED)
        with pytest.raises(InvalidStatusTransitionError):
            req.change_status(RequestStatus.WAITING_FOR_EMPLOYEE)

    def test_waiting_for_employee_in_enum(self):
        assert RequestStatus.WAITING_FOR_EMPLOYEE.value == "waiting_for_employee"

    def test_transition_map_includes_waiting(self):
        assert RequestStatus.WAITING_FOR_EMPLOYEE in VALID_STATUS_TRANSITIONS[RequestStatus.IN_PROGRESS]
        assert RequestStatus.IN_PROGRESS in VALID_STATUS_TRANSITIONS[RequestStatus.WAITING_FOR_EMPLOYEE]
        assert RequestStatus.RESOLVED in VALID_STATUS_TRANSITIONS[RequestStatus.WAITING_FOR_EMPLOYEE]
        assert RequestStatus.REJECTED in VALID_STATUS_TRANSITIONS[RequestStatus.WAITING_FOR_EMPLOYEE]


# ── SLA Pause/Resume ────────────────────────────────────────────

class TestSlaPauseResume:
    def test_entering_waiting_sets_sla_paused_at(self):
        req = _make_request(status=RequestStatus.IN_PROGRESS)
        assert req.sla_paused_at is None

        req.change_status(RequestStatus.WAITING_FOR_EMPLOYEE)

        assert req.sla_paused_at is not None
        assert req.sla_paused_total_seconds == 0

    def test_leaving_waiting_accumulates_paused_time(self):
        paused_at = datetime.now(timezone.utc) - timedelta(hours=1)
        req = _make_request(
            status=RequestStatus.WAITING_FOR_EMPLOYEE,
            sla_paused_at=paused_at,
            sla_paused_total_seconds=0,
        )

        req.change_status(RequestStatus.IN_PROGRESS)

        assert req.sla_paused_at is None
        # Should have ~3600 seconds (1 hour) accumulated
        assert 3500 <= req.sla_paused_total_seconds <= 3700

    def test_multiple_pause_cycles_accumulate(self):
        # First cycle: 1 hour already accumulated
        paused_at = datetime.now(timezone.utc) - timedelta(hours=2)
        req = _make_request(
            status=RequestStatus.WAITING_FOR_EMPLOYEE,
            sla_paused_at=paused_at,
            sla_paused_total_seconds=3600,  # 1h from previous cycle
        )

        req.change_status(RequestStatus.IN_PROGRESS)

        assert req.sla_paused_at is None
        # Should have ~3600 + ~7200 = ~10800 seconds (3h total)
        assert 10600 <= req.sla_paused_total_seconds <= 11000

    def test_waiting_to_resolved_accumulates_and_sets_resolved_at(self):
        paused_at = datetime.now(timezone.utc) - timedelta(hours=1)
        req = _make_request(
            status=RequestStatus.WAITING_FOR_EMPLOYEE,
            sla_paused_at=paused_at,
        )

        req.change_status(RequestStatus.RESOLVED)

        assert req.sla_paused_at is None
        assert 3500 <= req.sla_paused_total_seconds <= 3700
        assert req.resolved_at is not None

    def test_normal_transition_does_not_affect_sla_fields(self):
        req = _make_request(status=RequestStatus.IN_PROGRESS)
        req.change_status(RequestStatus.RESOLVED)

        assert req.sla_paused_at is None
        assert req.sla_paused_total_seconds == 0


# ── Auto-Transition (AddCommentHandler) ─────────────────────────

class TestAutoTransitionOnComment:
    def setup_method(self):
        self.request_repo = MagicMock()

    def test_comment_on_waiting_triggers_auto_transition(self):
        req = _make_request(status=RequestStatus.WAITING_FOR_EMPLOYEE)
        self.request_repo.find_by_id.return_value = req

        handler = AddCommentCommandHandler(request_repo=self.request_repo)
        handler.handle(AddCommentCommand(
            request_id="r1", company_id="c1",
            author_id="u_employee", body="Here is the info you needed",
        ))

        # Status should have changed to IN_PROGRESS
        assert req.status == RequestStatus.IN_PROGRESS
        # save_comment + save(request) calls
        assert self.request_repo.save_comment.call_count == 1
        assert self.request_repo.save.call_count == 1
        # Two events: comment_added + status_changed (auto)
        assert self.request_repo.save_event.call_count == 2
        auto_event_call = self.request_repo.save_event.call_args_list[1]
        event = auto_event_call[0][0]
        assert event.event_type == "status_changed"
        assert event.data["auto"] is True
        assert event.data["old_status"] == "waiting_for_employee"
        assert event.data["new_status"] == "in_progress"

    def test_comment_on_in_progress_no_transition(self):
        req = _make_request(status=RequestStatus.IN_PROGRESS)
        self.request_repo.find_by_id.return_value = req

        handler = AddCommentCommandHandler(request_repo=self.request_repo)
        handler.handle(AddCommentCommand(
            request_id="r1", company_id="c1",
            author_id="u_employee", body="Just checking in",
        ))

        assert req.status == RequestStatus.IN_PROGRESS
        # Only comment saved, no request save (no transition)
        assert self.request_repo.save.call_count == 0
        # Only one event: comment_added
        assert self.request_repo.save_event.call_count == 1

    def test_comment_on_submitted_no_transition(self):
        req = _make_request(status=RequestStatus.SUBMITTED)
        self.request_repo.find_by_id.return_value = req

        handler = AddCommentCommandHandler(request_repo=self.request_repo)
        handler.handle(AddCommentCommand(
            request_id="r1", company_id="c1",
            author_id="u_employee", body="Adding detail",
        ))

        assert req.status == RequestStatus.SUBMITTED
        assert self.request_repo.save.call_count == 0
        assert self.request_repo.save_event.call_count == 1

    def test_technician_comment_on_waiting_also_triggers_transition(self):
        """Any comment triggers auto-transition, not just employee."""
        req = _make_request(status=RequestStatus.WAITING_FOR_EMPLOYEE)
        self.request_repo.find_by_id.return_value = req

        handler = AddCommentCommandHandler(request_repo=self.request_repo)
        handler.handle(AddCommentCommand(
            request_id="r1", company_id="c1",
            author_id="u_technician", body="Actually, I found the answer",
        ))

        assert req.status == RequestStatus.IN_PROGRESS
        assert self.request_repo.save.call_count == 1


# ── SLA Query Paused Time ───────────────────────────────────────

class TestSlaQueryPausedTime:
    """Tests for SLA query subtracting paused time from resolution elapsed."""

    def setup_method(self):
        from src.sla_bc.sla.application.queries.get_request_sla import (
            GetRequestSlaStatusQuery,
            GetRequestSlaStatusQueryHandler,
        )
        from src.sla_bc.sla.domain.entities import SlaPolicy

        self.sla_repo = MagicMock()
        self.request_repo = MagicMock()
        self.handler = GetRequestSlaStatusQueryHandler(
            sla_repo=self.sla_repo,
            request_repo=self.request_repo,
        )
        self.query = GetRequestSlaStatusQuery(request_id="r1", company_id="c1")
        self.policy = SlaPolicy.create(
            company_id="c1",
            name="Test SLA",
            priority="high",
            response_time_hours=4,
            resolution_time_hours=24,
            warning_threshold_pct=75,
        )
        self.sla_repo.find_policy_for_request.return_value = self.policy

    def test_paused_time_subtracted_from_resolution(self):
        """4h total, 1h paused → resolution elapsed = ~3h."""
        req = _make_request(hours_ago=4, sla_paused_total_seconds=3600)
        self.request_repo.find_by_id.return_value = req

        result = self.handler.handle(self.query)

        assert result is not None
        # ~4h - 1h = ~3h
        assert 2.8 <= result.resolution_elapsed_hours <= 3.2

    def test_no_paused_time_unchanged(self):
        """4h total, 0h paused → resolution elapsed = ~4h."""
        req = _make_request(hours_ago=4, sla_paused_total_seconds=0)
        self.request_repo.find_by_id.return_value = req

        result = self.handler.handle(self.query)

        assert result is not None
        assert 3.8 <= result.resolution_elapsed_hours <= 4.2

    def test_active_pause_included(self):
        """Currently in waiting_for_employee for 2h → active pause deducted."""
        paused_at = datetime.now(timezone.utc) - timedelta(hours=2)
        req = _make_request(
            status=RequestStatus.WAITING_FOR_EMPLOYEE,
            hours_ago=4,
            sla_paused_at=paused_at,
            sla_paused_total_seconds=0,
        )
        self.request_repo.find_by_id.return_value = req

        result = self.handler.handle(self.query)

        assert result is not None
        # ~4h - ~2h active pause = ~2h
        assert 1.8 <= result.resolution_elapsed_hours <= 2.2

    def test_finalized_plus_active_pause(self):
        """2h finalized + 1h active = 3h total deducted from 6h."""
        paused_at = datetime.now(timezone.utc) - timedelta(hours=1)
        req = _make_request(
            status=RequestStatus.WAITING_FOR_EMPLOYEE,
            hours_ago=6,
            sla_paused_at=paused_at,
            sla_paused_total_seconds=7200,  # 2h finalized
        )
        self.request_repo.find_by_id.return_value = req

        result = self.handler.handle(self.query)

        assert result is not None
        # ~6h - ~3h = ~3h
        assert 2.8 <= result.resolution_elapsed_hours <= 3.2

    def test_resolution_elapsed_never_negative(self):
        """Edge case: more paused time than total → clamped to 0."""
        req = _make_request(hours_ago=1, sla_paused_total_seconds=7200)  # 2h paused > 1h total
        self.request_repo.find_by_id.return_value = req

        result = self.handler.handle(self.query)

        assert result is not None
        assert result.resolution_elapsed_hours == 0
