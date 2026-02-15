from src.notification_bc.notification.application.services.event_bus import EventBus
from src.notification_bc.notification.application.services.notification_subscriber import (
    NotificationSubscriber,
)
from src.notification_bc.notification.application.services.websocket_subscriber import (
    WebSocketSubscriber,
)

_event_bus = EventBus()
_event_bus.subscribe(NotificationSubscriber())
_event_bus.subscribe(WebSocketSubscriber())


def get_event_bus() -> EventBus:
    return _event_bus
