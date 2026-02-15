from unittest.mock import MagicMock

from src.notification_bc.notification.application.services.event_bus import EventBus
from src.notification_bc.notification.domain.events import DomainEvent


def _make_event(**overrides):
    defaults = dict(
        event_type="request.created",
        company_id="comp1",
        actor_id="user1",
        payload={},
        title="Test",
        body="Test body",
    )
    defaults.update(overrides)
    return DomainEvent(**defaults)


class TestEventBus:
    def test_publish_no_subscribers(self):
        bus = EventBus()
        event = _make_event()
        db = MagicMock()
        # Should not raise
        bus.publish(event, db)

    def test_publish_one_subscriber(self):
        bus = EventBus()
        subscriber = MagicMock()
        bus.subscribe(subscriber)

        event = _make_event()
        db = MagicMock()
        bus.publish(event, db)

        subscriber.assert_called_once_with(event, db)

    def test_publish_multiple_subscribers(self):
        bus = EventBus()
        sub1 = MagicMock()
        sub2 = MagicMock()
        bus.subscribe(sub1)
        bus.subscribe(sub2)

        event = _make_event()
        db = MagicMock()
        bus.publish(event, db)

        sub1.assert_called_once_with(event, db)
        sub2.assert_called_once_with(event, db)

    def test_subscriber_error_does_not_stop_others(self):
        bus = EventBus()
        sub1 = MagicMock(side_effect=RuntimeError("fail"))
        sub2 = MagicMock()
        bus.subscribe(sub1)
        bus.subscribe(sub2)

        event = _make_event()
        db = MagicMock()
        bus.publish(event, db)

        sub1.assert_called_once()
        sub2.assert_called_once()
