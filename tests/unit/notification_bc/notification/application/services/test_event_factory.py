from src.notification_bc.notification.application.services.event_factory import RequestEventFactory
from src.notification_bc.notification.domain.enums import EventType
from src.request_bc.request.domain.entities import ServiceRequest
from src.request_bc.request.domain.enums import RequestType


def _make_request(**overrides):
    defaults = dict(
        company_id="comp1",
        created_by="creator1",
        type=RequestType.INCIDENT,
        title="Laptop broken",
        description="Screen cracked",
    )
    defaults.update(overrides)
    return ServiceRequest.create(**defaults)


class TestRequestEventFactory:
    def test_request_created(self):
        request = _make_request()
        event = RequestEventFactory.request_created(request, actor_id="creator1")

        assert event.event_type == EventType.REQUEST_CREATED
        assert event.company_id == "comp1"
        assert event.actor_id == "creator1"
        assert event.payload["request_id"] == request.id
        assert event.payload["created_by"] == "creator1"
        assert event.payload["type"] == "incident"
        assert event.title == "New incident request"
        assert event.body == "Laptop broken"

    def test_status_changed(self):
        request = _make_request()
        event = RequestEventFactory.status_changed(
            request, old_status="submitted", new_status="in_review", actor_id="tech1",
        )

        assert event.event_type == EventType.REQUEST_STATUS_CHANGED
        assert event.actor_id == "tech1"
        assert event.payload["old_status"] == "submitted"
        assert event.payload["new_status"] == "in_review"
        assert event.payload["request_id"] == request.id
        assert event.payload["created_by"] == "creator1"
        assert "submitted" in event.body
        assert "in_review" in event.body

    def test_priority_changed(self):
        request = _make_request()
        event = RequestEventFactory.priority_changed(
            request, old_priority="high", new_priority="urgent", actor_id="tech1",
        )

        assert event.event_type == EventType.REQUEST_PRIORITY_CHANGED
        assert event.payload["old_priority"] == "high"
        assert event.payload["new_priority"] == "urgent"
        assert "high" in event.body
        assert "urgent" in event.body

    def test_request_assigned(self):
        request = _make_request()
        request.assign("tech1")
        event = RequestEventFactory.request_assigned(request, actor_id="admin1")

        assert event.event_type == EventType.REQUEST_ASSIGNED
        assert event.payload["assigned_to"] == "tech1"
        assert "tech1" in event.body

    def test_comment_added(self):
        request = _make_request()
        event = RequestEventFactory.comment_added(request, actor_id="creator1")

        assert event.event_type == EventType.REQUEST_COMMENT_ADDED
        assert event.payload["request_id"] == request.id
        assert event.payload["created_by"] == "creator1"
        assert event.title == "New comment"
        assert "Laptop broken" in event.body

    def test_note_added(self):
        request = _make_request()
        event = RequestEventFactory.note_added(request, actor_id="tech1")

        assert event.event_type == EventType.REQUEST_NOTE_ADDED
        assert event.payload["request_id"] == request.id
        assert event.title == "New internal note"
        assert "Laptop broken" in event.body

    def test_all_events_have_required_payload_fields(self):
        request = _make_request()
        request.assign("tech1")

        events = [
            RequestEventFactory.request_created(request, "actor1"),
            RequestEventFactory.status_changed(request, "submitted", "in_review", "actor1"),
            RequestEventFactory.priority_changed(request, "high", "urgent", "actor1"),
            RequestEventFactory.request_assigned(request, "actor1"),
            RequestEventFactory.comment_added(request, "actor1"),
            RequestEventFactory.note_added(request, "actor1"),
        ]

        for event in events:
            assert "request_id" in event.payload
            assert "created_by" in event.payload
            assert "assigned_to" in event.payload
            assert event.company_id == "comp1"
            assert event.timestamp is not None

    def test_new_equipment_title(self):
        request = _make_request(type=RequestType.NEW_EQUIPMENT, title="New monitor")
        event = RequestEventFactory.request_created(request, actor_id="user1")
        assert event.title == "New new equipment request"
