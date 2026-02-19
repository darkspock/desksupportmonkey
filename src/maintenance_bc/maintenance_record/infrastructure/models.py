from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from core.base import Base
from core.mixins import TimestampMixin, ULIDMixin


class MaintenanceRecordModel(ULIDMixin, TimestampMixin, Base):
    __tablename__ = "maintenance_records"

    company_id: Mapped[str] = mapped_column(
        String(26),
        ForeignKey("companies.id"),
        index=True,
    )
    asset_id: Mapped[str] = mapped_column(
        String(26),
        ForeignKey("assets.id"),
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        server_default="SCHEDULED",
        index=True,
    )
    priority: Mapped[str] = mapped_column(String(20), index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    technician_id: Mapped[Optional[str]] = mapped_column(
        String(26),
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )
    template_id: Mapped[Optional[str]] = mapped_column(
        String(26),
        ForeignKey("maintenance_templates.id"),
        nullable=True,
        index=True,
    )
    plan_id: Mapped[Optional[str]] = mapped_column(
        String(26),
        ForeignKey("maintenance_plans.id"),
        nullable=True,
        index=True,
    )
    checklist_items: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        index=True,
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completion_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    actual_findings: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cancellation_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    skip_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reminder_48h_sent: Mapped[bool] = mapped_column(
        Boolean,
        server_default="false",
    )
    overdue_alert_sent: Mapped[bool] = mapped_column(
        Boolean,
        server_default="false",
    )
