from sqlalchemy.orm import Session

from src.auth_bc.user.infrastructure.repository import UserRepository
from src.notification_bc.notification.application.services.target_resolver import TargetResolver
from src.notification_bc.notification.domain.entities import Notification
from src.notification_bc.notification.domain.events import DomainEvent
from src.notification_bc.notification.infrastructure.repository import NotificationRepository


class NotificationSubscriber:
    def __call__(self, event: DomainEvent, db: Session) -> None:
        resolver = TargetResolver(user_repo=UserRepository(db))
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

        repo = NotificationRepository(db)
        repo.save_batch(notifications)
