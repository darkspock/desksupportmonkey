from datetime import datetime

from dateutil.relativedelta import relativedelta

from src.maintenance_bc.maintenance_record.domain.enums import (
    RecurrenceFrequency,
)


def compute_next_due(
    base: datetime,
    frequency: RecurrenceFrequency,
    interval: int,
) -> datetime:
    if interval < 1:
        raise ValueError("recurrence interval must be >= 1")

    if frequency == RecurrenceFrequency.DAILY:
        return base + relativedelta(days=interval)
    if frequency == RecurrenceFrequency.WEEKLY:
        return base + relativedelta(weeks=interval)
    if frequency == RecurrenceFrequency.MONTHLY:
        return base + relativedelta(months=interval)
    if frequency == RecurrenceFrequency.QUARTERLY:
        return base + relativedelta(months=3 * interval)
    if frequency == RecurrenceFrequency.YEARLY:
        return base + relativedelta(years=interval)

    raise ValueError(f"Unsupported recurrence frequency: {frequency}")
