from src.auth_bc.user.infrastructure.repository import UserRepository
from src.notification_bc.notification.application.services.event_bus import EventBus
from src.notification_bc.notification.application.services.notification_subscriber import (
    NotificationSubscriber,
)
from src.notification_bc.notification.application.services.websocket_subscriber import (
    WebSocketSubscriber,
)
from src.notification_bc.notification.infrastructure.repository import NotificationRepository

_event_bus = EventBus()
_event_bus.subscribe(
    NotificationSubscriber(
        user_repo_factory=UserRepository,
        notification_repo_factory=NotificationRepository,
    )
)
_event_bus.subscribe(
    WebSocketSubscriber(
        user_repo_factory=UserRepository,
        notification_repo_factory=NotificationRepository,
    )
)


def get_event_bus() -> EventBus:
    return _event_bus
