import asyncio
import logging

from sqlalchemy.orm import Session

from src.auth_bc.user.infrastructure.repository import UserRepository
from src.notification_bc.notification.application.services.target_resolver import TargetResolver
from src.notification_bc.notification.domain.events import DomainEvent
from src.notification_bc.notification.infrastructure.connection_manager import connection_manager
from src.notification_bc.notification.infrastructure.repository import NotificationRepository

logger = logging.getLogger(__name__)


class WebSocketSubscriber:
    def __call__(self, event: DomainEvent, db: Session) -> None:
        resolver = TargetResolver(user_repo=UserRepository(db))
        target_ids = resolver.resolve(event)
        if not target_ids:
            return

        # Filter to only connected users
        connected_targets = [uid for uid in target_ids if connection_manager.is_connected(uid)]
        if not connected_targets:
            return

        notification_repo = NotificationRepository(db)

        notification_message = {
            "type": "notification",
            "data": {
                "event_type": event.event_type,
                "title": event.title,
                "body": event.body,
                "data": event.payload,
                "created_at": event.timestamp.isoformat(),
            },
        }

        for uid in connected_targets:
            unread_count = notification_repo.count_unread(uid)
            unread_message = {
                "type": "unread_count",
                "data": {"count": unread_count},
            }

            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(
                        self._send_to_user(uid, notification_message, unread_message)
                    )
                else:
                    loop.run_until_complete(
                        self._send_to_user(uid, notification_message, unread_message)
                    )
            except RuntimeError:
                # No event loop available — skip WebSocket push
                logger.debug("No event loop available for WebSocket push to user %s", uid)

    @staticmethod
    async def _send_to_user(user_id: str, notification_msg: dict, unread_msg: dict) -> None:
        await connection_manager.send_to_user(user_id, notification_msg)
        await connection_manager.send_to_user(user_id, unread_msg)
