from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Index, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from core.base import Base
from core.mixins import ULIDMixin


class NotificationModel(ULIDMixin, Base):
    __tablename__ = "notifications"

    user_id: Mapped[str] = mapped_column(String(26), index=True)
    company_id: Mapped[str] = mapped_column(String(26))
    event_type: Mapped[str] = mapped_column(String(50))
    title: Mapped[str] = mapped_column(String(255))
    body: Mapped[str] = mapped_column(Text)
    data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    is_read: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("ix_notifications_user_read_created", "user_id", "is_read", "created_at"),
    )
