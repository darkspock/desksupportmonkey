from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from core.base import Base
from core.mixins import TimestampMixin, ULIDMixin


class MaintenanceTemplateModel(ULIDMixin, TimestampMixin, Base):
    __tablename__ = "maintenance_templates"

    company_id: Mapped[str] = mapped_column(
        String(26),
        ForeignKey("companies.id"),
        index=True,
    )
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    default_priority: Mapped[str] = mapped_column(String(20))
    recurrence_frequency: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )
    recurrence_interval: Mapped[int] = mapped_column(
        Integer,
        server_default="1",
    )
    asset_type_filter: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        server_default="true",
    )

    checklist_items: Mapped[list["MaintenanceChecklistItemModel"]] = relationship(
        "MaintenanceChecklistItemModel",
        cascade="all, delete-orphan",
        order_by="MaintenanceChecklistItemModel.sort_order",
    )


class MaintenanceChecklistItemModel(ULIDMixin, Base):
    __tablename__ = "maintenance_checklist_items"

    template_id: Mapped[str] = mapped_column(
        String(26),
        ForeignKey("maintenance_templates.id", ondelete="CASCADE"),
        index=True,
    )
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_required: Mapped[bool] = mapped_column(
        Boolean,
        server_default="true",
    )
    sort_order: Mapped[int] = mapped_column(
        Integer,
        server_default="0",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
    )


class MaintenancePlanModel(ULIDMixin, TimestampMixin, Base):
    __tablename__ = "maintenance_plans"

    company_id: Mapped[str] = mapped_column(
        String(26),
        ForeignKey("companies.id"),
        index=True,
    )
    template_id: Mapped[str] = mapped_column(
        String(26),
        ForeignKey("maintenance_templates.id"),
        index=True,
    )
    asset_id: Mapped[str] = mapped_column(
        String(26),
        ForeignKey("assets.id"),
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        server_default="true",
    )
    next_due_at: Mapped[datetime] = mapped_column(
        DateTime,
        index=True,
    )
    last_generated_at: Mapped[Optional[datetime]] = (
        mapped_column(
            DateTime,
            nullable=True,
        )
    )
