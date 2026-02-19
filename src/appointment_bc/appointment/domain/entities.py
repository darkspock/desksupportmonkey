from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date as Date, datetime, time, timedelta
from typing import Optional

import ulid

from src.appointment_bc.appointment.domain.enums import (
    AppointmentStatus,
    InvalidAppointmentStatusTransitionError,
    VALID_TRANSITIONS,
)

ALLOWED_DURATIONS = {30, 60, 90}


@dataclass
class Appointment:
    id: str
    company_id: str
    request_id: str
    technician_id: str
    employee_id: str
    status: AppointmentStatus
    scheduled_start: datetime
    scheduled_end: datetime
    duration_minutes: int
    created_by: str
    location: Optional[str] = None
    notes: Optional[str] = None
    cancellation_reason: Optional[str] = None
    cancelled_by: Optional[str] = None
    rescheduled_from_id: Optional[str] = None
    reminder_24h_sent: bool = False
    reminder_1h_sent: bool = False
    completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        company_id: str,
        request_id: str,
        technician_id: str,
        employee_id: str,
        scheduled_start: datetime,
        duration_minutes: int,
        created_by: str,
        initial_status: AppointmentStatus = AppointmentStatus.PENDING,
        location: Optional[str] = None,
        rescheduled_from_id: Optional[str] = None,
        id: Optional[str] = None,
    ) -> "Appointment":
        if duration_minutes not in ALLOWED_DURATIONS:
            raise ValueError(
                f"Duration must be one of {sorted(ALLOWED_DURATIONS)}, "
                f"got {duration_minutes}"
            )
        scheduled_end = scheduled_start + timedelta(
            minutes=duration_minutes,
        )
        return cls(
            id=id or str(ulid.new()),
            company_id=company_id,
            request_id=request_id,
            technician_id=technician_id,
            employee_id=employee_id,
            status=initial_status,
            scheduled_start=scheduled_start,
            scheduled_end=scheduled_end,
            duration_minutes=duration_minutes,
            created_by=created_by,
            location=location,
            rescheduled_from_id=rescheduled_from_id,
        )

    def _transition(self, target: AppointmentStatus) -> None:
        allowed = VALID_TRANSITIONS.get(self.status, [])
        if target not in allowed:
            raise InvalidAppointmentStatusTransitionError(
                self.status, target,
            )
        self.status = target

    def confirm(self) -> None:
        self._transition(AppointmentStatus.CONFIRMED)

    def cancel(
        self, reason: str, cancelled_by: str,
    ) -> None:
        self._transition(AppointmentStatus.CANCELLED)
        self.cancellation_reason = reason
        self.cancelled_by = cancelled_by

    def complete(
        self, notes: Optional[str] = None,
    ) -> None:
        self._transition(AppointmentStatus.COMPLETED)
        self.completed_at = datetime.now(UTC)
        if notes:
            self.notes = notes

    def mark_no_show(self) -> None:
        self._transition(AppointmentStatus.NO_SHOW)

    def mark_reminder_sent(
        self, reminder_type: str,
    ) -> None:
        if reminder_type == "24h":
            self.reminder_24h_sent = True
        elif reminder_type == "1h":
            self.reminder_1h_sent = True
        else:
            raise ValueError(
                f"Invalid reminder type: {reminder_type}"
            )


@dataclass
class TechnicianAvailability:
    id: str
    company_id: str
    technician_id: str
    day_of_week: int
    start_time: time
    end_time: time
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        company_id: str,
        technician_id: str,
        day_of_week: int,
        start_time: time,
        end_time: time,
        id: Optional[str] = None,
    ) -> "TechnicianAvailability":
        if day_of_week not in range(7):
            raise ValueError(
                f"day_of_week must be 0-6, got {day_of_week}"
            )
        if start_time >= end_time:
            raise ValueError(
                "start_time must be before end_time"
            )
        return cls(
            id=id or str(ulid.new()),
            company_id=company_id,
            technician_id=technician_id,
            day_of_week=day_of_week,
            start_time=start_time,
            end_time=end_time,
        )


@dataclass
class AvailabilityOverride:
    id: str
    company_id: str
    technician_id: str
    date: Date
    is_available: bool
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    reason: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        company_id: str,
        technician_id: str,
        target_date: Date,
        is_available: bool,
        start_time: Optional[time] = None,
        end_time: Optional[time] = None,
        reason: Optional[str] = None,
        id: Optional[str] = None,
    ) -> AvailabilityOverride:
        if is_available:
            if start_time is None or end_time is None:
                raise ValueError(
                    "start_time and end_time are required "
                    "when is_available is True"
                )
            if start_time >= end_time:
                raise ValueError(
                    "start_time must be before end_time"
                )
        return cls(
            id=id or str(ulid.new()),
            company_id=company_id,
            technician_id=technician_id,
            date=target_date,
            is_available=is_available,
            start_time=start_time,
            end_time=end_time,
            reason=reason,
        )
