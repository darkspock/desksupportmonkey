from dataclasses import dataclass

from src.framework.application.command_bus import Command, CommandHandler
from src.notification_bc.notification.domain.repository import NotificationRepositoryInterface


class NotificationNotFoundError(Exception):
    def __init__(self, notification_id: str):
        super().__init__(f"Notification {notification_id} not found")
        self.notification_id = notification_id


@dataclass
class MarkReadCommand(Command):
    notification_id: str
    user_id: str


class MarkReadCommandHandler(CommandHandler[MarkReadCommand]):
    def __init__(self, notification_repo: NotificationRepositoryInterface):
        self.notification_repo = notification_repo

    def handle(self, command: MarkReadCommand) -> None:
        found = self.notification_repo.mark_read(command.notification_id, command.user_id)
        if not found:
            raise NotificationNotFoundError(command.notification_id)
