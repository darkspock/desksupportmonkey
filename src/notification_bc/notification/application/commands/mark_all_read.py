from dataclasses import dataclass

from src.framework.application.command_bus import Command, CommandHandler
from src.notification_bc.notification.domain.repository import NotificationRepositoryInterface


@dataclass
class MarkAllReadCommand(Command):
    user_id: str


class MarkAllReadCommandHandler(CommandHandler[MarkAllReadCommand]):
    def __init__(self, notification_repo: NotificationRepositoryInterface):
        self.notification_repo = notification_repo

    def handle(self, command: MarkAllReadCommand) -> None:
        self.notification_repo.mark_all_read(command.user_id)
