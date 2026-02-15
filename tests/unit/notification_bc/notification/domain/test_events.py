from datetime import datetime, timezone

import pytest

from src.notification_bc.notification.domain.events import DomainEvent


class TestDomainEvent:
    def test_create_with_all_fields(self):
        event = DomainEvent(
            event_type="request.created",
            company_id="comp1",
            actor_id="user1",
            payload={"request_id": "req1", "created_by": "user1"},
            title="New request",
            body="A new incident request",
        )
        assert event.event_type == "request.created"
        assert event.company_id == "comp1"
        assert event.actor_id == "user1"
        assert event.payload["request_id"] == "req1"
        assert event.title == "New request"
        assert event.body == "A new incident request"
        assert event.timestamp is not None

    def test_frozen_immutable(self):
        event = DomainEvent(
            event_type="request.created",
            company_id="comp1",
            actor_id="user1",
            payload={},
            title="Title",
            body="Body",
        )
        with pytest.raises(AttributeError):
            event.event_type = "request.updated"

    def test_default_timestamp(self):
        before = datetime.now(timezone.utc)
        event = DomainEvent(
            event_type="request.created",
            company_id="comp1",
            actor_id="user1",
            payload={},
            title="Title",
            body="Body",
        )
        after = datetime.now(timezone.utc)
        assert before <= event.timestamp <= after
