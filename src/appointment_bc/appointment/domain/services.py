from __future__ import annotations

from dataclasses import dataclass
from datetime import date, time

from src.appointment_bc.appointment.domain.entities import (
    Appointment,
    AvailabilityOverride,
    TechnicianAvailability,
)
from src.appointment_bc.appointment.domain.enums import (
    AppointmentStatus,
)


@dataclass(frozen=True)
class TimeSlot:
    start: time
    end: time


# Type alias for internal window representation
Window = tuple[time, time]

DEFAULT_WEEKDAY_WINDOWS: list[Window] = [
    (time(9, 0), time(12, 0)),
    (time(14, 0), time(17, 0)),
]


class AvailabilityService:

    @staticmethod
    def compute_available_slots(
        target_date: date,
        duration_minutes: int,
        recurring_windows: list[TechnicianAvailability],
        overrides: list[AvailabilityOverride],
        existing_appointments: list[Appointment],
    ) -> list[TimeSlot]:
        weekday = target_date.weekday()

        # 1. Get recurring windows for this day
        day_windows: list[Window] = [
            (w.start_time, w.end_time)
            for w in recurring_windows
            if w.day_of_week == weekday
        ]

        # 2. Apply defaults if no recurring windows
        if not day_windows:
            if weekday < 5:  # Mon-Fri
                day_windows = list(DEFAULT_WEEKDAY_WINDOWS)
            else:
                day_windows = []

        # 3. Apply overrides
        for override in overrides:
            if not override.is_available:
                if (
                    override.start_time is None
                    or override.end_time is None
                ):
                    # Block entire day
                    day_windows = []
                else:
                    # Subtract blocked range
                    day_windows = (
                        AvailabilityService._subtract_range(
                            day_windows,
                            override.start_time,
                            override.end_time,
                        )
                    )
            else:
                # Add extra availability window
                if (
                    override.start_time is not None
                    and override.end_time is not None
                ):
                    day_windows.append(
                        (
                            override.start_time,
                            override.end_time,
                        )
                    )

        # 4. Subtract existing CONFIRMED appointments
        for appt in existing_appointments:
            if appt.status == AppointmentStatus.CONFIRMED:
                appt_start = appt.scheduled_start.time()
                appt_end = appt.scheduled_end.time()
                day_windows = (
                    AvailabilityService._subtract_range(
                        day_windows, appt_start, appt_end,
                    )
                )

        # 5. Sort windows
        day_windows.sort(key=lambda w: w[0])

        # 6. Split into bookable slots
        return AvailabilityService._split_into_slots(
            day_windows, duration_minutes,
        )

    @staticmethod
    def _subtract_range(
        windows: list[Window],
        block_start: time,
        block_end: time,
    ) -> list[Window]:
        result: list[Window] = []
        for w_start, w_end in windows:
            if block_end <= w_start or block_start >= w_end:
                # No overlap
                result.append((w_start, w_end))
            else:
                # Partial overlap — keep parts outside block
                if w_start < block_start:
                    result.append((w_start, block_start))
                if block_end < w_end:
                    result.append((block_end, w_end))
        return result

    @staticmethod
    def _split_into_slots(
        windows: list[Window],
        duration_minutes: int,
    ) -> list[TimeSlot]:
        slots: list[TimeSlot] = []
        for w_start, w_end in windows:
            current = w_start
            while True:
                total_minutes = (
                    current.hour * 60 + current.minute
                ) + duration_minutes
                if total_minutes > 24 * 60:
                    break
                next_hour = total_minutes // 60
                next_minute = total_minutes % 60
                next_time = time(next_hour, next_minute)
                if next_time > w_end:
                    break
                slots.append(TimeSlot(
                    start=current, end=next_time,
                ))
                current = next_time
        return slots
