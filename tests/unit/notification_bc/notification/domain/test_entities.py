import pytest

from src.notification_bc.notification.domain.entities import Notification
from src.notification_bc.notification.domain.enums import EventType


class TestNotification:
    def test_create_valid(self):
        n = Notification.create(
            user_id="user1",
            company_id="comp1",
            event_type=EventType.REQUEST_CREATED,
            title="New request",
            body="A new incident request was created",
            data={"request_id": "req1"},
        )
        assert n.id is not None
        assert n.user_id == "user1"
        assert n.company_id == "comp1"
        assert n.event_type == EventType.REQUEST_CREATED
        assert n.title == "New request"
        assert n.body == "A new incident request was created"
        assert n.data == {"request_id": "req1"}
        assert n.is_read is False
        assert n.created_at is None

    def test_create_empty_title_raises(self):
        with pytest.raises(ValueError, match="Title is required"):
            Notification.create(
                user_id="user1",
                company_id="comp1",
                event_type=EventType.REQUEST_CREATED,
                title="",
                body="Some body",
            )

    def test_create_empty_body_raises(self):
        with pytest.raises(ValueError, match="Body is required"):
            Notification.create(
                user_id="user1",
                company_id="comp1",
                event_type=EventType.REQUEST_CREATED,
                title="Some title",
                body="",
            )

    def test_create_whitespace_title_raises(self):
        with pytest.raises(ValueError, match="Title is required"):
            Notification.create(
                user_id="user1",
                company_id="comp1",
                event_type=EventType.REQUEST_CREATED,
                title="   ",
                body="Some body",
            )

    def test_create_strips_whitespace(self):
        n = Notification.create(
            user_id="user1",
            company_id="comp1",
            event_type=EventType.REQUEST_CREATED,
            title="  Title  ",
            body="  Body  ",
        )
        assert n.title == "Title"
        assert n.body == "Body"

    def test_create_without_data(self):
        n = Notification.create(
            user_id="user1",
            company_id="comp1",
            event_type=EventType.REQUEST_STATUS_CHANGED,
            title="Status changed",
            body="In review",
        )
        assert n.data is None

    def test_default_is_read_false(self):
        n = Notification.create(
            user_id="user1",
            company_id="comp1",
            event_type=EventType.REQUEST_ASSIGNED,
            title="Assigned",
            body="You were assigned",
        )
        assert n.is_read is False


class TestEventType:
    def test_values(self):
        assert EventType.REQUEST_CREATED == "request.created"
        assert EventType.REQUEST_STATUS_CHANGED == "request.status_changed"
        assert EventType.REQUEST_ASSIGNED == "request.assigned"
        assert EventType.REQUEST_PRIORITY_CHANGED == "request.priority_changed"
        assert EventType.REQUEST_COMMENT_ADDED == "request.comment_added"
        assert EventType.REQUEST_NOTE_ADDED == "request.note_added"

    def test_count(self):
        assert len(EventType) == 7
