from abc import ABC, abstractmethod
from datetime import date
from typing import Optional

from src.notification_bc.notification.domain.entities import Notification


class NotificationRepositoryInterface(ABC):

    @abstractmethod
    def save(self, notification: Notification) -> Notification: ...

    @abstractmethod
    def save_batch(self, notifications: list[Notification]) -> None: ...

    @abstractmethod
    def find_by_user(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
        is_read: Optional[bool] = None,
    ) -> tuple[list[Notification], int]: ...

    @abstractmethod
    def count_unread(self, user_id: str) -> int: ...

    @abstractmethod
    def mark_read(self, notification_id: str, user_id: str) -> bool: ...

    @abstractmethod
    def mark_all_read(self, user_id: str) -> int: ...

    @abstractmethod
    def find_by_data_key(
        self,
        event_type: str,
        data_key: str,
        data_value: str,
        date_check: date,
    ) -> bool: ...
