from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from core.base import Base
from core.mixins import TimestampMixin, ULIDMixin


class SlaPolicyModel(ULIDMixin, TimestampMixin, Base):
    __tablename__ = "sla_policies"

    company_id: Mapped[str] = mapped_column(String(26), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    priority: Mapped[str] = mapped_column(String(10), nullable=False)
    request_type: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    response_time_hours: Mapped[float] = mapped_column(Float, nullable=False)
    resolution_time_hours: Mapped[float] = mapped_column(Float, nullable=False)
    warning_threshold_pct: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="75"
    )
    escalate_on_breach: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )

    __table_args__ = (
        Index("ix_sla_policies_company_active", "company_id", "is_active"),
        Index(
            "ix_sla_policies_company_priority_type_active",
            "company_id",
            "priority",
            "request_type",
            "is_active",
        ),
        UniqueConstraint(
            "company_id",
            "priority",
            "request_type",
            name="uq_sla_policies_company_priority_type",
        ),
    )


class SlaBreachRecordModel(ULIDMixin, Base):
    __tablename__ = "sla_breach_records"

    company_id: Mapped[str] = mapped_column(String(26), nullable=False)
    request_id: Mapped[str] = mapped_column(String(26), nullable=False)
    policy_id: Mapped[str] = mapped_column(String(26), nullable=False)
    breach_type: Mapped[str] = mapped_column(String(30), nullable=False)
    target_hours: Mapped[float] = mapped_column(Float, nullable=False)
    actual_hours: Mapped[float] = mapped_column(Float, nullable=False)
    escalated: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        Index("ix_sla_breaches_company_created", "company_id", "created_at"),
        Index("ix_sla_breaches_request", "request_id"),
        UniqueConstraint(
            "request_id",
            "breach_type",
            name="uq_sla_breaches_request_type",
        ),
    )
