from typing import Optional

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from src.notification_bc.notification.domain.entities import Notification
from src.notification_bc.notification.domain.repository import NotificationRepositoryInterface
from src.notification_bc.notification.infrastructure.models import NotificationModel


class NotificationRepository(NotificationRepositoryInterface):
    def __init__(self, session: Session):
        self.session = session

    def save(self, notification: Notification) -> Notification:
        model = NotificationModel(
            id=notification.id,
            user_id=notification.user_id,
            company_id=notification.company_id,
            event_type=notification.event_type,
            title=notification.title,
            body=notification.body,
            data=notification.data,
            is_read=notification.is_read,
        )
        self.session.add(model)
        self.session.flush()
        self.session.refresh(model)
        return self._to_entity(model)

    def save_batch(self, notifications: list[Notification]) -> None:
        models = [
            NotificationModel(
                id=n.id,
                user_id=n.user_id,
                company_id=n.company_id,
                event_type=n.event_type,
                title=n.title,
                body=n.body,
                data=n.data,
                is_read=n.is_read,
            )
            for n in notifications
        ]
        self.session.add_all(models)
        self.session.flush()

    def find_by_user(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
        is_read: Optional[bool] = None,
    ) -> tuple[list[Notification], int]:
        stmt = select(NotificationModel).where(NotificationModel.user_id == user_id)

        if is_read is not None:
            stmt = stmt.where(NotificationModel.is_read == is_read)

        total = self.session.execute(
            select(func.count()).select_from(stmt.subquery())
        ).scalar()

        stmt = stmt.order_by(NotificationModel.created_at.desc())
        offset = (page - 1) * page_size
        models = self.session.execute(
            stmt.offset(offset).limit(page_size)
        ).scalars().all()

        return [self._to_entity(m) for m in models], total

    def count_unread(self, user_id: str) -> int:
        result = self.session.execute(
            select(func.count()).select_from(NotificationModel).where(
                NotificationModel.user_id == user_id,
                NotificationModel.is_read == False,  # noqa: E712
            )
        ).scalar()
        return result or 0

    def mark_read(self, notification_id: str, user_id: str) -> bool:
        result = self.session.execute(
            update(NotificationModel)
            .where(
                NotificationModel.id == notification_id,
                NotificationModel.user_id == user_id,
            )
            .values(is_read=True)
        )
        self.session.flush()
        return result.rowcount > 0

    def mark_all_read(self, user_id: str) -> int:
        result = self.session.execute(
            update(NotificationModel)
            .where(
                NotificationModel.user_id == user_id,
                NotificationModel.is_read == False,  # noqa: E712
            )
            .values(is_read=True)
        )
        self.session.flush()
        return result.rowcount

    @staticmethod
    def _to_entity(model: NotificationModel) -> Notification:
        return Notification(
            id=model.id,
            user_id=model.user_id,
            company_id=model.company_id,
            event_type=model.event_type,
            title=model.title,
            body=model.body,
            data=model.data,
            is_read=model.is_read,
            created_at=model.created_at,
        )
