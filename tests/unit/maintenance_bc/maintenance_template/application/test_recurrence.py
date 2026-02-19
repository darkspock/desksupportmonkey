from datetime import UTC, datetime

from src.maintenance_bc.maintenance_record.domain.enums import (
    RecurrenceFrequency,
)
from src.maintenance_bc.maintenance_template.application.services.recurrence import (
    compute_next_due,
)


def test_compute_next_due_monthly():
    base = datetime(2026, 1, 31, 8, 0, tzinfo=UTC)
    next_due = compute_next_due(base, RecurrenceFrequency.MONTHLY, 1)
    assert next_due.month == 2


def test_compute_next_due_quarterly():
    base = datetime(2026, 1, 1, 8, 0, tzinfo=UTC)
    next_due = compute_next_due(base, RecurrenceFrequency.QUARTERLY, 1)
    assert next_due.month == 4
