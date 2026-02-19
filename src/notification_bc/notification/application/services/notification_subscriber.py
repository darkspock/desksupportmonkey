from typing import Callable

from sqlalchemy.orm import Session

from src.notification_bc.notification.application.ports import UserLookup
from src.notification_bc.notification.application.services.target_resolver import TargetResolver
from src.notification_bc.notification.domain.entities import Notification
from src.notification_bc.notification.domain.events import DomainEvent
from src.notification_bc.notification.domain.repository import NotificationRepositoryInterface


class NotificationSubscriber:
    def __init__(
        self,
        user_repo_factory: Callable[[Session], UserLookup],
        notification_repo_factory: Callable[[Session], NotificationRepositoryInterface],
    ):
        self._user_repo_factory = user_repo_factory
        self._notification_repo_factory = notification_repo_factory

    def __call__(self, event: DomainEvent, db: Session) -> None:
        resolver = TargetResolver(user_repo=self._user_repo_factory(db))
        target_ids = resolver.resolve(event)
        if not target_ids:
            return

        notifications = [
            Notification.create(
                user_id=uid,
                company_id=event.company_id,
                event_type=event.event_type,
                title=event.title,
                body=event.body,
                data=event.payload,
            )
            for uid in target_ids
        ]

        repo = self._notification_repo_factory(db)
        repo.save_batch(notifications)
