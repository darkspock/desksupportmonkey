from unittest.mock import MagicMock, patch

from src.notification_bc.notification.application.services.notification_subscriber import (
    NotificationSubscriber,
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


class TestNotificationSubscriber:
    @patch("src.notification_bc.notification.application.services.notification_subscriber.TargetResolver")
    def test_creates_notifications_for_targets(self, MockResolver):
        mock_resolver_instance = MockResolver.return_value
        mock_resolver_instance.resolve.return_value = ["creator1", "tech1"]

        mock_user_repo_factory = MagicMock()
        mock_notif_repo = MagicMock()
        mock_notif_repo_factory = MagicMock(return_value=mock_notif_repo)

        subscriber = NotificationSubscriber(
            user_repo_factory=mock_user_repo_factory,
            notification_repo_factory=mock_notif_repo_factory,
        )
        event = _make_event()
        db = MagicMock()

        subscriber(event, db)

        mock_notif_repo.save_batch.assert_called_once()
        notifications = mock_notif_repo.save_batch.call_args[0][0]
        assert len(notifications) == 2
        user_ids = {n.user_id for n in notifications}
        assert user_ids == {"creator1", "tech1"}
        for n in notifications:
            assert n.event_type == EventType.REQUEST_STATUS_CHANGED
            assert n.title == "Request updated"
            assert n.company_id == "comp1"

    @patch("src.notification_bc.notification.application.services.notification_subscriber.TargetResolver")
    def test_noop_when_no_targets(self, MockResolver):
        mock_resolver_instance = MockResolver.return_value
        mock_resolver_instance.resolve.return_value = []

        mock_user_repo_factory = MagicMock()
        mock_notif_repo = MagicMock()
        mock_notif_repo_factory = MagicMock(return_value=mock_notif_repo)

        subscriber = NotificationSubscriber(
            user_repo_factory=mock_user_repo_factory,
            notification_repo_factory=mock_notif_repo_factory,
        )
        event = _make_event(actor_id="tech1")
        db = MagicMock()

        subscriber(event, db)

        mock_notif_repo.save_batch.assert_not_called()
