from dataclasses import dataclass
from typing import Optional

from src.framework.application.query_bus import Query, QueryHandler
from src.notification_bc.notification.domain.entities import Notification
from src.notification_bc.notification.domain.repository import NotificationRepositoryInterface


@dataclass
class ListNotificationsQuery(Query):
    user_id: str
    page: int = 1
    page_size: int = 20
    is_read: Optional[bool] = None


class ListNotificationsQueryHandler(QueryHandler[ListNotificationsQuery, tuple[list[Notification], int, int]]):
    def __init__(self, notification_repo: NotificationRepositoryInterface):
        self.notification_repo = notification_repo

    def handle(self, query: ListNotificationsQuery) -> tuple[list[Notification], int, int]:
        """Returns (notifications, total, unread_count)."""
        notifications, total = self.notification_repo.find_by_user(
            user_id=query.user_id,
            page=query.page,
            page_size=query.page_size,
            is_read=query.is_read,
        )
        unread_count = self.notification_repo.count_unread(query.user_id)
        return notifications, total, unread_count
