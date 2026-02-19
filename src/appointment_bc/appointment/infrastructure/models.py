from datetime import date, datetime, time
from typing import Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from core.base import Base
from core.mixins import TimestampMixin, ULIDMixin


class AppointmentModel(ULIDMixin, TimestampMixin, Base):
    __tablename__ = "appointments"

    company_id: Mapped[str] = mapped_column(
        String(26),
        ForeignKey("companies.id"),
        index=True,
    )
    request_id: Mapped[str] = mapped_column(
        String(26),
        ForeignKey("service_requests.id"),
        index=True,
    )
    technician_id: Mapped[str] = mapped_column(
        String(26),
        ForeignKey("users.id"),
        index=True,
    )
    employee_id: Mapped[str] = mapped_column(
        String(26),
        ForeignKey("users.id"),
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(20), server_default="PENDING",
    )
    scheduled_start: Mapped[datetime] = mapped_column(
        DateTime,
    )
    scheduled_end: Mapped[datetime] = mapped_column(
        DateTime,
    )
    duration_minutes: Mapped[int] = mapped_column(
        Integer, server_default="60",
    )
    location: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
    )
    cancellation_reason: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
    )
    cancelled_by: Mapped[Optional[str]] = mapped_column(
        String(26), nullable=True,
    )
    rescheduled_from_id: Mapped[Optional[str]] = mapped_column(
        String(26),
        ForeignKey("appointments.id"),
        nullable=True,
    )
    reminder_24h_sent: Mapped[bool] = mapped_column(
        Boolean, server_default="false",
    )
    reminder_1h_sent: Mapped[bool] = mapped_column(
        Boolean, server_default="false",
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True,
    )
    created_by: Mapped[str] = mapped_column(String(26))


class TechnicianAvailabilityModel(
    ULIDMixin, TimestampMixin, Base,
):
    __tablename__ = "technician_availabilities"

    company_id: Mapped[str] = mapped_column(
        String(26),
        ForeignKey("companies.id"),
        index=True,
    )
    technician_id: Mapped[str] = mapped_column(
        String(26),
        ForeignKey("users.id"),
        index=True,
    )
    day_of_week: Mapped[int] = mapped_column(Integer)
    start_time: Mapped[time] = mapped_column(Time)
    end_time: Mapped[time] = mapped_column(Time)

    __table_args__ = (
        UniqueConstraint(
            "technician_id",
            "day_of_week",
            "start_time",
            name="uq_availability_tech_day_start",
        ),
    )


class AvailabilityOverrideModel(
    ULIDMixin, TimestampMixin, Base,
):
    __tablename__ = "availability_overrides"

    company_id: Mapped[str] = mapped_column(
        String(26),
        ForeignKey("companies.id"),
        index=True,
    )
    technician_id: Mapped[str] = mapped_column(
        String(26),
        ForeignKey("users.id"),
        index=True,
    )
    date: Mapped[date] = mapped_column(Date)
    is_available: Mapped[bool] = mapped_column(
        Boolean, server_default="false",
    )
    start_time: Mapped[Optional[time]] = mapped_column(
        Time, nullable=True,
    )
    end_time: Mapped[Optional[time]] = mapped_column(
        Time, nullable=True,
    )
    reason: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
    )

    __table_args__ = (
        UniqueConstraint(
            "technician_id",
            "date",
            "start_time",
            name="uq_override_tech_date_start",
        ),
    )
