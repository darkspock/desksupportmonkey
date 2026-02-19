from dataclasses import dataclass
from typing import Optional

from src.framework.application.command_bus import Command, CommandHandler
from src.notification_bc.notification.domain.entities import Notification
from src.notification_bc.notification.domain.repository import NotificationRepositoryInterface


@dataclass
class CreateNotificationCommand(Command):
    user_id: str
    company_id: str
    event_type: str
    title: str
    body: str
    data: Optional[dict] = None


class CreateNotificationCommandHandler(CommandHandler[CreateNotificationCommand]):
    def __init__(self, notification_repo: NotificationRepositoryInterface):
        self.notification_repo = notification_repo

    def handle(self, command: CreateNotificationCommand) -> None:
        notification = Notification.create(
            user_id=command.user_id,
            company_id=command.company_id,
            event_type=command.event_type,
            title=command.title,
            body=command.body,
            data=command.data,
        )
        self.notification_repo.save(notification)
