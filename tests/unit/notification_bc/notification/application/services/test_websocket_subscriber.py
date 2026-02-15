from unittest.mock import AsyncMock, MagicMock, patch

from src.notification_bc.notification.application.services.websocket_subscriber import (
    WebSocketSubscriber,
)
from src.notification_bc.notification.domain.enums import EventType
from src.notification_bc.notification.domain.events import DomainEvent


def _make_event(event_type=EventType.REQUEST_STATUS_CHANGED, actor_id="actor1"):
    return DomainEvent(
        event_type=event_type,
        company_id="comp1",
        actor_id=actor_id,
        payload={"request_id": "req1", "created_by": "creator1", "assigned_to": "tech1"},
        title="Request updated",
        body="Status changed",
    )


class TestWebSocketSubscriber:
    @patch("src.notification_bc.notification.application.services.websocket_subscriber.NotificationRepository")
    @patch("src.notification_bc.notification.application.services.websocket_subscriber.UserRepository")
    @patch("src.notification_bc.notification.application.services.websocket_subscriber.TargetResolver")
    @patch("src.notification_bc.notification.application.services.websocket_subscriber.connection_manager")
    def test_noop_when_no_targets(self, mock_cm, MockResolver, MockUserRepo, MockNotifRepo):
        mock_resolver_instance = MockResolver.return_value
        mock_resolver_instance.resolve.return_value = []

        subscriber = WebSocketSubscriber()
        event = _make_event()
        db = MagicMock()

        subscriber(event, db)

        # No send attempts since no targets
        mock_cm.send_to_user.assert_not_called()

    @patch("src.notification_bc.notification.application.services.websocket_subscriber.NotificationRepository")
    @patch("src.notification_bc.notification.application.services.websocket_subscriber.UserRepository")
    @patch("src.notification_bc.notification.application.services.websocket_subscriber.TargetResolver")
    @patch("src.notification_bc.notification.application.services.websocket_subscriber.connection_manager")
    def test_noop_when_no_connected_users(self, mock_cm, MockResolver, MockUserRepo, MockNotifRepo):
        mock_resolver_instance = MockResolver.return_value
        mock_resolver_instance.resolve.return_value = ["creator1", "tech1"]
        mock_cm.is_connected.return_value = False

        subscriber = WebSocketSubscriber()
        event = _make_event()
        db = MagicMock()

        subscriber(event, db)

        mock_cm.send_to_user.assert_not_called()
