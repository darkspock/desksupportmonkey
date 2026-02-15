from datetime import datetime
from typing import Any, Optional

from sqlalchemy import DateTime, ForeignKey, Index, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from core.base import Base
from core.mixins import ULIDMixin, TimestampMixin


class ReportModel(ULIDMixin, TimestampMixin, Base):
    __tablename__ = "reports"

    company_id: Mapped[str] = mapped_column(String(26), ForeignKey("companies.id"))
    requested_by: Mapped[str] = mapped_column(String(26), ForeignKey("users.id"))
    type: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(20), server_default="pending")
    parameters: Mapped[Optional[Any]] = mapped_column(JSON)
    storage_key: Mapped[Optional[str]] = mapped_column(String(500))
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    __table_args__ = (
        Index("ix_reports_company_created", "company_id", "created_at"),
    )
