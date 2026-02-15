from dataclasses import dataclass

from src.notification_bc.notification.domain.repository import NotificationRepositoryInterface


class NotificationNotFoundError(Exception):
    def __init__(self, notification_id: str):
        super().__init__(f"Notification {notification_id} not found")
        self.notification_id = notification_id


@dataclass
class MarkReadCommand:
    notification_id: str
    user_id: str


class MarkReadCommandHandler:
    def __init__(self, notification_repo: NotificationRepositoryInterface):
        self.notification_repo = notification_repo

    def handle(self, command: MarkReadCommand) -> None:
        found = self.notification_repo.mark_read(command.notification_id, command.user_id)
        if not found:
            raise NotificationNotFoundError(command.notification_id)
