import logging
from typing import Callable

from sqlalchemy.orm import Session

from src.notification_bc.notification.domain.events import DomainEvent

logger = logging.getLogger(__name__)


class EventBus:
    def __init__(self):
        self._subscribers: list[Callable] = []

    def subscribe(self, subscriber: Callable) -> None:
        self._subscribers.append(subscriber)

    def publish(self, event: DomainEvent, db: Session) -> None:
        for subscriber in self._subscribers:
            try:
                subscriber(event, db)
            except Exception:
                logger.exception(
                    "Event subscriber %s failed for event %s",
                    subscriber.__class__.__name__ if hasattr(subscriber, '__class__') else str(subscriber),
                    event.event_type,
                )
