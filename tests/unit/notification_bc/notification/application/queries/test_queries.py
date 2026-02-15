from unittest.mock import MagicMock

from src.notification_bc.notification.application.queries.list_notifications import (
    ListNotificationsQuery,
    ListNotificationsQueryHandler,
)
from src.notification_bc.notification.domain.entities import Notification
from src.notification_bc.notification.domain.enums import EventType


def _make_notification(**overrides):
    defaults = dict(
        user_id="user1",
        company_id="comp1",
        event_type=EventType.REQUEST_CREATED,
        title="Test notification",
        body="Test body",
    )
    defaults.update(overrides)
    return Notification.create(**defaults)


class TestListNotificationsQuery:
    def test_returns_paginated_with_unread_count(self):
        notifications = [_make_notification(title=f"Notif {i}") for i in range(3)]
        repo = MagicMock()
        repo.find_by_user.return_value = (notifications, 3)
        repo.count_unread.return_value = 2
        handler = ListNotificationsQueryHandler(notification_repo=repo)

        result, total, unread_count = handler.handle(
            ListNotificationsQuery(user_id="user1", page=1, page_size=20)
        )

        assert len(result) == 3
        assert total == 3
        assert unread_count == 2
        repo.find_by_user.assert_called_once_with(
            user_id="user1", page=1, page_size=20, is_read=None
        )
        repo.count_unread.assert_called_once_with("user1")

    def test_with_is_read_filter(self):
        repo = MagicMock()
        repo.find_by_user.return_value = ([], 0)
        repo.count_unread.return_value = 0
        handler = ListNotificationsQueryHandler(notification_repo=repo)

        handler.handle(
            ListNotificationsQuery(user_id="user1", is_read=False)
        )

        call_kwargs = repo.find_by_user.call_args.kwargs
        assert call_kwargs["is_read"] is False

    def test_empty_results(self):
        repo = MagicMock()
        repo.find_by_user.return_value = ([], 0)
        repo.count_unread.return_value = 0
        handler = ListNotificationsQueryHandler(notification_repo=repo)

        result, total, unread_count = handler.handle(
            ListNotificationsQuery(user_id="user1")
        )

        assert result == []
        assert total == 0
        assert unread_count == 0
