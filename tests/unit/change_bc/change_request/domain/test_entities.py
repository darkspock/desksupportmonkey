import pytest

from src.change_bc.change_request.domain.entities import (
    ChangeEvent,
    ChangeRequest,
    PostImplementationReview,
)
from src.change_bc.change_request.domain.enums import (
    ChangeEventType,
    ChangeStatus,
    ChangeType,
    InvalidStatusTransitionError,
    PIROutcome,
)
from src.change_bc.change_request.domain.exceptions import (
    ChangeNotEditableError,
    RejectionReasonRequiredError,
    RollbackPlanRequiredError,
    RollbackReasonRequiredError,
)


def _make_change(**overrides) -> ChangeRequest:
    defaults = dict(
        id="01CHANGE000000000000000001",
        company_id="01COMPANY00000000000000001",
        requested_by="01USER00000000000000000001",
        title="Install security patch",
    )
    defaults.update(overrides)
    return ChangeRequest.create(**defaults)


class TestChangeRequestCreate:
    def test_sets_draft_status(self):
        change = _make_change()
        assert change.status == ChangeStatus.DRAFT

    def test_stores_id(self):
        change = _make_change()
        assert change.id == "01CHANGE000000000000000001"

    def test_default_type_is_standard(self):
        change = _make_change()
        assert change.change_type == ChangeType.STANDARD

    def test_validates_title_required(self):
        with pytest.raises(ValueError, match="Title is required"):
            _make_change(title="")

    def test_validates_whitespace_title(self):
        with pytest.raises(ValueError, match="Title is required"):
            _make_change(title="   ")

    def test_strips_title(self):
        change = _make_change(title="  padded  ")
        assert change.title == "padded"

    def test_optional_fields_are_none(self):
        change = _make_change()
        assert change.description is None
        assert change.assigned_to is None
        assert change.approved_by is None
        assert change.implemented_at is None


class TestChangeRequestSubmit:
    def test_standard_auto_approves_to_scheduled(self):
        change = _make_change(change_type=ChangeType.STANDARD)
        change.submit()
        assert change.status == ChangeStatus.SCHEDULED

    def test_normal_goes_to_pending_approval(self):
        change = _make_change(change_type=ChangeType.NORMAL)
        change.rollback_plan = "Restore from backup"
        change.submit()
        assert change.status == ChangeStatus.PENDING_APPROVAL

    def test_emergency_goes_to_pending_approval(self):
        change = _make_change(change_type=ChangeType.EMERGENCY)
        change.rollback_plan = "Revert config"
        change.submit()
        assert change.status == ChangeStatus.PENDING_APPROVAL

    def test_normal_requires_rollback_plan(self):
        change = _make_change(change_type=ChangeType.NORMAL)
        with pytest.raises(RollbackPlanRequiredError):
            change.submit()

    def test_emergency_requires_rollback_plan(self):
        change = _make_change(change_type=ChangeType.EMERGENCY)
        with pytest.raises(RollbackPlanRequiredError):
            change.submit()

    def test_standard_does_not_require_rollback_plan(self):
        change = _make_change(change_type=ChangeType.STANDARD)
        change.submit()  # should not raise

    def test_submit_from_non_draft_raises(self):
        change = _make_change()
        change.submit()  # standard → SCHEDULED
        with pytest.raises(InvalidStatusTransitionError):
            change.submit()


class TestChangeRequestApprove:
    def test_approve_sets_scheduled(self):
        change = _make_change(change_type=ChangeType.NORMAL)
        change.rollback_plan = "Plan"
        change.submit()
        change.approve("admin1")
        assert change.status == ChangeStatus.SCHEDULED

    def test_approve_records_fields(self):
        change = _make_change(change_type=ChangeType.NORMAL)
        change.rollback_plan = "Plan"
        change.submit()
        change.approve("admin1")
        assert change.approved_by == "admin1"
        assert change.approved_at is not None

    def test_approve_from_non_pending_raises(self):
        change = _make_change()  # DRAFT
        with pytest.raises(InvalidStatusTransitionError):
            change.approve("admin1")


class TestChangeRequestReject:
    def test_reject_sets_rejected(self):
        change = _make_change(change_type=ChangeType.NORMAL)
        change.rollback_plan = "Plan"
        change.submit()
        change.reject("admin1", "Not justified")
        assert change.status == ChangeStatus.REJECTED

    def test_reject_records_fields(self):
        change = _make_change(change_type=ChangeType.NORMAL)
        change.rollback_plan = "Plan"
        change.submit()
        change.reject("admin1", "Too risky")
        assert change.rejected_by == "admin1"
        assert change.rejected_at is not None
        assert change.rejection_reason == "Too risky"

    def test_reject_requires_reason(self):
        change = _make_change(change_type=ChangeType.NORMAL)
        change.rollback_plan = "Plan"
        change.submit()
        with pytest.raises(RejectionReasonRequiredError):
            change.reject("admin1", "")

    def test_reject_requires_non_whitespace_reason(self):
        change = _make_change(change_type=ChangeType.NORMAL)
        change.rollback_plan = "Plan"
        change.submit()
        with pytest.raises(RejectionReasonRequiredError):
            change.reject("admin1", "   ")


class TestChangeRequestStart:
    def test_start_sets_in_progress(self):
        change = _make_change()
        change.submit()  # SCHEDULED
        change.start()
        assert change.status == ChangeStatus.IN_PROGRESS

    def test_start_records_started_at(self):
        change = _make_change()
        change.submit()
        change.start()
        assert change.started_at is not None

    def test_start_from_non_scheduled_raises(self):
        change = _make_change()  # DRAFT
        with pytest.raises(InvalidStatusTransitionError):
            change.start()


class TestChangeRequestImplement:
    def test_implement_sets_implemented(self):
        change = _make_change()
        change.submit()
        change.start()
        change.implement()
        assert change.status == ChangeStatus.IMPLEMENTED

    def test_implement_records_fields(self):
        change = _make_change()
        change.submit()
        change.start()
        change.implement(notes="All OK")
        assert change.implemented_at is not None
        assert change.implementation_notes == "All OK"

    def test_implement_notes_optional(self):
        change = _make_change()
        change.submit()
        change.start()
        change.implement()
        assert change.implementation_notes is None


class TestChangeRequestRollback:
    def test_rollback_from_in_progress(self):
        change = _make_change()
        change.submit()
        change.start()
        change.rollback("Failed deployment")
        assert change.status == ChangeStatus.ROLLED_BACK

    def test_rollback_from_implemented(self):
        change = _make_change()
        change.submit()
        change.start()
        change.implement()
        change.rollback("Issues found")
        assert change.status == ChangeStatus.ROLLED_BACK

    def test_rollback_records_fields(self):
        change = _make_change()
        change.submit()
        change.start()
        change.rollback("Reason here")
        assert change.rolled_back_at is not None
        assert change.rollback_reason == "Reason here"

    def test_rollback_requires_reason(self):
        change = _make_change()
        change.submit()
        change.start()
        with pytest.raises(RollbackReasonRequiredError):
            change.rollback("")

    def test_rollback_requires_non_whitespace_reason(self):
        change = _make_change()
        change.submit()
        change.start()
        with pytest.raises(RollbackReasonRequiredError):
            change.rollback("   ")


class TestChangeRequestClose:
    def test_close_sets_closed(self):
        change = _make_change()
        change.submit()
        change.start()
        change.implement()
        change.close()
        assert change.status == ChangeStatus.CLOSED

    def test_close_records_closed_at(self):
        change = _make_change()
        change.submit()
        change.start()
        change.implement()
        change.close()
        assert change.closed_at is not None

    def test_close_from_non_implemented_raises(self):
        change = _make_change()
        change.submit()
        change.start()
        with pytest.raises(InvalidStatusTransitionError):
            change.close()


class TestChangeRequestUpdateDetails:
    def test_update_in_draft(self):
        change = _make_change()
        change.update_details(title="New title", description="Desc")
        assert change.title == "New title"
        assert change.description == "Desc"

    def test_update_in_pending_approval(self):
        change = _make_change(change_type=ChangeType.NORMAL)
        change.rollback_plan = "Plan"
        change.submit()
        change.update_details(description="Updated")
        assert change.description == "Updated"

    def test_update_in_scheduled_raises(self):
        change = _make_change()
        change.submit()  # SCHEDULED
        with pytest.raises(ChangeNotEditableError):
            change.update_details(title="X")

    def test_update_empty_title_raises(self):
        change = _make_change()
        with pytest.raises(ValueError, match="Title cannot be empty"):
            change.update_details(title="   ")

    def test_update_only_provided_fields(self):
        change = _make_change()
        original_title = change.title
        change.update_details(description="Only desc")
        assert change.title == original_title
        assert change.description == "Only desc"


class TestChangeRequestAssign:
    def test_assign_in_draft(self):
        change = _make_change()
        change.assign("tech1")
        assert change.assigned_to == "tech1"

    def test_assign_in_scheduled(self):
        change = _make_change()
        change.submit()
        change.assign("tech2")
        assert change.assigned_to == "tech2"

    def test_assign_in_in_progress(self):
        change = _make_change()
        change.submit()
        change.start()
        change.assign("tech3")
        assert change.assigned_to == "tech3"

    def test_assign_in_terminal_raises(self):
        change = _make_change()
        change.submit()
        change.start()
        change.implement()
        change.close()
        with pytest.raises(InvalidStatusTransitionError):
            change.assign("tech1")


class TestChangeEvent:
    def test_create_generates_ulid(self):
        event = ChangeEvent.create(
            change_request_id="cr1",
            event_type=ChangeEventType.CREATED,
            description="Created",
            actor_id="user1",
        )
        assert event.id is not None
        assert len(event.id) == 26

    def test_create_stores_fields(self):
        event = ChangeEvent.create(
            change_request_id="cr1",
            event_type=ChangeEventType.APPROVED,
            description="Approved",
            actor_id="admin1",
            metadata={"notes": "looks good"},
        )
        assert event.change_request_id == "cr1"
        assert event.event_type == ChangeEventType.APPROVED
        assert event.description == "Approved"
        assert event.actor_id == "admin1"
        assert event.metadata == {"notes": "looks good"}


class TestPostImplementationReview:
    def test_create_sets_all_fields(self):
        pir = PostImplementationReview.create(
            change_request_id="cr1",
            outcome=PIROutcome.SUCCESSFUL,
            created_by="admin1",
            issues_found="None",
            lessons_learned="Deploy earlier",
            follow_up_actions="Monitor for 24h",
        )
        assert pir.change_request_id == "cr1"
        assert pir.outcome == PIROutcome.SUCCESSFUL
        assert isinstance(pir.outcome, PIROutcome)
        assert pir.created_by == "admin1"
        assert pir.issues_found == "None"
        assert pir.lessons_learned == "Deploy earlier"
        assert pir.follow_up_actions == "Monitor for 24h"

    def test_create_generates_ulid_id(self):
        pir = PostImplementationReview.create(
            change_request_id="cr1",
            outcome=PIROutcome.PARTIAL,
            created_by="admin1",
        )
        assert pir.id is not None
        assert len(pir.id) == 26

    def test_create_optional_fields_default_none(self):
        pir = PostImplementationReview.create(
            change_request_id="cr1",
            outcome=PIROutcome.FAILED,
            created_by="admin1",
        )
        assert pir.issues_found is None
        assert pir.lessons_learned is None
        assert pir.follow_up_actions is None

    def test_create_preserves_optional_fields(self):
        pir = PostImplementationReview.create(
            change_request_id="cr1",
            outcome=PIROutcome.SUCCESSFUL,
            created_by="admin1",
            issues_found="Disk space issue",
            lessons_learned="Pre-check storage",
            follow_up_actions="Add monitoring alert",
        )
        assert pir.issues_found == "Disk space issue"
        assert pir.lessons_learned == "Pre-check storage"
        assert pir.follow_up_actions == "Add monitoring alert"
