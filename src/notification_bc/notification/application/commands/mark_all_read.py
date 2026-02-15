from dataclasses import dataclass

from src.notification_bc.notification.domain.repository import NotificationRepositoryInterface


@dataclass
class MarkAllReadCommand:
    user_id: str


class MarkAllReadCommandHandler:
    def __init__(self, notification_repo: NotificationRepositoryInterface):
        self.notification_repo = notification_repo

    def handle(self, command: MarkAllReadCommand) -> int:
        return self.notification_repo.mark_all_read(command.user_id)
