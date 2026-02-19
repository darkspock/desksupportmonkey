from unittest.mock import MagicMock

import pytest

from src.notification_bc.notification.application.commands.create_notification import (
    CreateNotificationCommand,
    CreateNotificationCommandHandler,
)
from src.notification_bc.notification.application.commands.mark_all_read import (
    MarkAllReadCommand,
    MarkAllReadCommandHandler,
)
from src.notification_bc.notification.application.commands.mark_read import (
    MarkReadCommand,
    MarkReadCommandHandler,
    NotificationNotFoundError,
)
from src.notification_bc.notification.domain.entities import Notification
from src.notification_bc.notification.domain.enums import EventType


class TestCreateNotificationCommand:
    def test_success(self):
        repo = MagicMock()
        repo.save.side_effect = lambda n: n
        handler = CreateNotificationCommandHandler(notification_repo=repo)

        handler.handle(
            CreateNotificationCommand(
                user_id="user1",
                company_id="comp1",
                event_type=EventType.REQUEST_CREATED,
                title="New request",
                body="A new request was created",
                data={"request_id": "req1"},
            )
        )

        repo.save.assert_called_once()


class TestMarkReadCommand:
    def test_success(self):
        repo = MagicMock()
        repo.mark_read.return_value = True
        handler = MarkReadCommandHandler(notification_repo=repo)

        handler.handle(MarkReadCommand(notification_id="notif1", user_id="user1"))

        repo.mark_read.assert_called_once_with("notif1", "user1")

    def test_not_found_raises(self):
        repo = MagicMock()
        repo.mark_read.return_value = False
        handler = MarkReadCommandHandler(notification_repo=repo)

        with pytest.raises(NotificationNotFoundError):
            handler.handle(MarkReadCommand(notification_id="bad", user_id="user1"))


class TestMarkAllReadCommand:
    def test_success(self):
        repo = MagicMock()
        repo.mark_all_read.return_value = 5
        handler = MarkAllReadCommandHandler(notification_repo=repo)

        handler.handle(MarkAllReadCommand(user_id="user1"))

        repo.mark_all_read.assert_called_once_with("user1")

    def test_zero_unread(self):
        repo = MagicMock()
        repo.mark_all_read.return_value = 0
        handler = MarkAllReadCommandHandler(notification_repo=repo)

        handler.handle(MarkAllReadCommand(user_id="user1"))

        repo.mark_all_read.assert_called_once_with("user1")
