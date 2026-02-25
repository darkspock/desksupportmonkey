import pytest

from src.request_bc.request.domain.entities import (
    RequestComment,
    RequestEvent,
    RequestNote,
    ServiceRequest,
)
from src.request_bc.request.domain.enums import (
    InvalidStatusTransitionError,
    RequestPriority,
    RequestStatus,
    RequestType,
)


class TestServiceRequestCreate:
    def test_create_incident_auto_priority_high(self):
        req = ServiceRequest.create(
            company_id="comp1",
            created_by="user1",
            type=RequestType.INCIDENT,
            title="Laptop broken",
            description="Screen is cracked",
        )
        assert req.priority == RequestPriority.HIGH
        assert req.status == RequestStatus.SUBMITTED
        assert req.type == RequestType.INCIDENT
        assert req.title == "Laptop broken"
        assert req.assigned_to is None
        assert req.resolved_at is None
        assert len(req.id) == 26

    def test_create_new_equipment_auto_priority_low(self):
        req = ServiceRequest.create(
            company_id="comp1",
            created_by="user1",
            type=RequestType.NEW_EQUIPMENT,
            title="Need monitor",
            description="Second monitor for dev work",
        )
        assert req.priority == RequestPriority.LOW

    def test_create_onboarding_auto_priority_medium(self):
        req = ServiceRequest.create(
            company_id="comp1",
            created_by="user1",
            type=RequestType.ONBOARDING,
            title="New hire setup",
            description="Setup for John Doe",
        )
        assert req.priority == RequestPriority.MEDIUM

    def test_create_with_data(self):
        req = ServiceRequest.create(
            company_id="comp1",
            created_by="user1",
            type=RequestType.INCIDENT,
            title="Laptop broken",
            description="Screen cracked",
            data={"asset_id": "asset123"},
        )
        assert req.data == {"asset_id": "asset123"}

    def test_create_empty_title_raises(self):
        with pytest.raises(ValueError, match="Title is required"):
            ServiceRequest.create(
                company_id="comp1",
                created_by="user1",
                type=RequestType.INCIDENT,
                title="",
                description="Something",
            )

    def test_create_empty_description_raises(self):
        with pytest.raises(ValueError, match="Description is required"):
            ServiceRequest.create(
                company_id="comp1",
                created_by="user1",
                type=RequestType.INCIDENT,
                title="Title",
                description="",
            )

    def test_create_whitespace_title_raises(self):
        with pytest.raises(ValueError, match="Title is required"):
            ServiceRequest.create(
                company_id="comp1",
                created_by="user1",
                type=RequestType.INCIDENT,
                title="   ",
                description="Something",
            )

    def test_create_strips_whitespace(self):
        req = ServiceRequest.create(
            company_id="comp1",
            created_by="user1",
            type=RequestType.INCIDENT,
            title="  Laptop broken  ",
            description="  Screen cracked  ",
        )
        assert req.title == "Laptop broken"
        assert req.description == "Screen cracked"


class TestServiceRequestWorkflowTemplate:
    def test_create_with_workflow_template_id(self):
        req = ServiceRequest.create(
            company_id="comp1",
            created_by="user1",
            type=RequestType.INCIDENT,
            title="Test",
            description="Test desc",
            workflow_template_id="tmpl_123",
        )
        assert req.workflow_template_id == "tmpl_123"
        assert req.workflow_subtype_id is None

    def test_create_with_workflow_template_and_subtype_ids(self):
        req = ServiceRequest.create(
            company_id="comp1",
            created_by="user1",
            type=RequestType.NEW_EQUIPMENT,
            title="Need laptop",
            description="For work",
            workflow_template_id="tmpl_456",
            workflow_subtype_id="sub_789",
            subtype="Computer",
        )
        assert req.workflow_template_id == "tmpl_456"
        assert req.workflow_subtype_id == "sub_789"
        assert req.subtype == "Computer"

    def test_create_with_template_skips_subtype_enum_validation(self):
        """When workflow_template_id is set, subtype validation against enum is skipped."""
        req = ServiceRequest.create(
            company_id="comp1",
            created_by="user1",
            type=RequestType.INCIDENT,
            title="Test",
            description="Test desc",
            workflow_template_id="tmpl_123",
            subtype="CustomSubtype",  # would fail enum validation without template
        )
        assert req.subtype == "CustomSubtype"

    def test_create_without_template_fields_backward_compatible(self):
        req = ServiceRequest.create(
            company_id="comp1",
            created_by="user1",
            type=RequestType.INCIDENT,
            title="Test",
            description="Test desc",
        )
        assert req.workflow_template_id is None
        assert req.workflow_subtype_id is None


class TestServiceRequestChangeStatus:
    def _make_request(self, status=RequestStatus.SUBMITTED):
        req = ServiceRequest.create(
            company_id="comp1",
            created_by="user1",
            type=RequestType.INCIDENT,
            title="Test",
            description="Test desc",
        )
        req.status = status
        return req

    def test_submitted_to_in_review(self):
        req = self._make_request(RequestStatus.SUBMITTED)
        req.change_status(RequestStatus.IN_REVIEW)
        assert req.status == RequestStatus.IN_REVIEW

    def test_in_review_to_in_progress(self):
        req = self._make_request(RequestStatus.IN_REVIEW)
        req.change_status(RequestStatus.IN_PROGRESS)
        assert req.status == RequestStatus.IN_PROGRESS

    def test_in_review_to_rejected(self):
        req = self._make_request(RequestStatus.IN_REVIEW)
        req.change_status(RequestStatus.REJECTED)
        assert req.status == RequestStatus.REJECTED

    def test_in_progress_to_resolved(self):
        req = self._make_request(RequestStatus.IN_PROGRESS)
        req.change_status(RequestStatus.RESOLVED)
        assert req.status == RequestStatus.RESOLVED

    def test_in_progress_back_to_in_review(self):
        req = self._make_request(RequestStatus.IN_PROGRESS)
        req.change_status(RequestStatus.IN_REVIEW)
        assert req.status == RequestStatus.IN_REVIEW

    def test_resolved_sets_resolved_at(self):
        req = self._make_request(RequestStatus.IN_PROGRESS)
        assert req.resolved_at is None
        req.change_status(RequestStatus.RESOLVED)
        assert req.resolved_at is not None

    def test_rejected_sets_resolved_at(self):
        req = self._make_request(RequestStatus.IN_REVIEW)
        req.change_status(RequestStatus.REJECTED)
        assert req.resolved_at is not None

    def test_invalid_transition_raises(self):
        req = self._make_request(RequestStatus.SUBMITTED)
        with pytest.raises(InvalidStatusTransitionError):
            req.change_status(RequestStatus.RESOLVED)

    def test_terminal_state_raises(self):
        req = self._make_request(RequestStatus.RESOLVED)
        with pytest.raises(InvalidStatusTransitionError):
            req.change_status(RequestStatus.IN_REVIEW)


class TestServiceRequestChangePriority:
    def test_change_priority(self):
        req = ServiceRequest.create(
            company_id="comp1",
            created_by="user1",
            type=RequestType.NEW_EQUIPMENT,
            title="Need mouse",
            description="Mouse broken",
        )
        assert req.priority == RequestPriority.LOW
        req.change_priority(RequestPriority.URGENT)
        assert req.priority == RequestPriority.URGENT


class TestServiceRequestAssign:
    def test_assign(self):
        req = ServiceRequest.create(
            company_id="comp1",
            created_by="user1",
            type=RequestType.INCIDENT,
            title="Test",
            description="Test",
        )
        assert req.assigned_to is None
        req.assign("tech1")
        assert req.assigned_to == "tech1"


class TestRequestEvent:
    def test_create_event(self):
        event = RequestEvent.create(
            request_id="req1",
            event_type="created",
            data={"type": "incident"},
            performed_by="user1",
        )
        assert len(event.id) == 26
        assert event.request_id == "req1"
        assert event.event_type == "created"
        assert event.data == {"type": "incident"}
        assert event.performed_by == "user1"


class TestRequestComment:
    def test_create_comment(self):
        comment = RequestComment.create(
            request_id="req1",
            author_id="user1",
            body="This is a comment",
        )
        assert len(comment.id) == 26
        assert comment.body == "This is a comment"

    def test_create_empty_body_raises(self):
        with pytest.raises(ValueError, match="Comment body is required"):
            RequestComment.create(request_id="req1", author_id="user1", body="")

    def test_create_whitespace_body_raises(self):
        with pytest.raises(ValueError, match="Comment body is required"):
            RequestComment.create(request_id="req1", author_id="user1", body="   ")

    def test_create_strips_whitespace(self):
        comment = RequestComment.create(
            request_id="req1", author_id="user1", body="  hello  "
        )
        assert comment.body == "hello"


class TestRequestNote:
    def test_create_note(self):
        note = RequestNote.create(
            request_id="req1",
            author_id="tech1",
            body="Internal note",
        )
        assert len(note.id) == 26
        assert note.body == "Internal note"

    def test_create_empty_body_raises(self):
        with pytest.raises(ValueError, match="Note body is required"):
            RequestNote.create(request_id="req1", author_id="tech1", body="")

    def test_create_strips_whitespace(self):
        note = RequestNote.create(
            request_id="req1", author_id="tech1", body="  note  "
        )
        assert note.body == "note"
