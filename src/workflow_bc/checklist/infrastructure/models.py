from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from core.base import Base
from core.mixins import ULIDMixin


class RequestChecklistItemModel(ULIDMixin, Base):
    __tablename__ = "request_checklist_items"

    request_id: Mapped[str] = mapped_column(
        String(26), ForeignKey("service_requests.id", ondelete="CASCADE"), nullable=False
    )
    require_all_complete: Mapped[bool] = mapped_column(Boolean, server_default="false")
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    assignee_id: Mapped[Optional[str]] = mapped_column(String(26), nullable=True)
    is_required: Mapped[bool] = mapped_column(Boolean, server_default="true")
    is_completed: Mapped[bool] = mapped_column(Boolean, server_default="false")
    completed_by: Mapped[Optional[str]] = mapped_column(String(26), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("ix_request_checklist_items_request", "request_id"),
        Index("ix_request_checklist_items_assignee", "assignee_id", "is_completed"),
    )
