from datetime import UTC, datetime

import pytest

from src.maintenance_bc.maintenance_record.domain.entities import (
    MaintenanceRecord,
)
from src.maintenance_bc.maintenance_record.domain.enums import (
    InvalidMaintenanceStatusTransitionError,
    MaintenancePriority,
    MaintenanceStatus,
)


class TestMaintenanceRecordCreate:

    def test_create_defaults_to_scheduled(self):
        record = MaintenanceRecord.create(
            company_id="c1",
            asset_id="a1",
            title="Replace filter",
        )
        assert record.status == MaintenanceStatus.SCHEDULED
        assert record.priority == MaintenancePriority.MEDIUM
        assert record.reminder_48h_sent is False
        assert record.overdue_alert_sent is False

    def test_create_with_optional_fields(self):
        scheduled_at = datetime(2026, 3, 1, 8, 0, tzinfo=UTC)
        record = MaintenanceRecord.create(
            company_id="c1",
            asset_id="a1",
            title="Battery check",
            priority=MaintenancePriority.HIGH,
            description="Quarterly check",
            technician_id="u1",
            template_id="t1",
            plan_id="p1",
            checklist_items=["Open cover", "Check battery"],
            scheduled_at=scheduled_at,
        )
        assert record.priority == MaintenancePriority.HIGH
        assert record.technician_id == "u1"
        assert record.template_id == "t1"
        assert record.plan_id == "p1"
        assert len(record.checklist_items) == 2
        assert record.scheduled_at == scheduled_at

    def test_create_requires_title(self):
        with pytest.raises(ValueError, match="title"):
            MaintenanceRecord.create(
                company_id="c1",
                asset_id="a1",
                title="",
            )


class TestMaintenanceRecordAssignment:

    def _make_record(self) -> MaintenanceRecord:
        return MaintenanceRecord.create(
            company_id="c1",
            asset_id="a1",
            title="Filter change",
        )

    def test_assign_technician(self):
        record = self._make_record()
        record.assign("tech-1")
        assert record.technician_id == "tech-1"

    def test_assign_requires_technician(self):
        record = self._make_record()
        with pytest.raises(ValueError, match="technician_id"):
            record.assign("")

    def test_assign_disallowed_in_terminal_status(self):
        record = self._make_record()
        record.cancel("No longer needed")
        with pytest.raises(ValueError, match="terminal"):
            record.assign("tech-1")


class TestMaintenanceRecordTransitions:

    def _scheduled_record(self, technician_id: str | None = "tech-1") -> MaintenanceRecord:
        return MaintenanceRecord.create(
            company_id="c1",
            asset_id="a1",
            title="Filter change",
            technician_id=technician_id,
        )

    def test_start_requires_technician(self):
        record = self._scheduled_record(technician_id=None)
        with pytest.raises(ValueError, match="without technician"):
            record.start()

    def test_start_moves_to_in_progress(self):
        record = self._scheduled_record()
        record.start()
        assert record.status == MaintenanceStatus.IN_PROGRESS
        assert record.started_at is not None

    def test_start_from_in_progress_raises(self):
        record = self._scheduled_record()
        record.start()
        with pytest.raises(InvalidMaintenanceStatusTransitionError):
            record.start()

    def test_complete_from_in_progress(self):
        record = self._scheduled_record()
        record.start()
        record.complete(
            completion_notes="Done",
            actual_findings="No issues",
        )
        assert record.status == MaintenanceStatus.COMPLETED
        assert record.completed_at is not None
        assert record.completion_notes == "Done"
        assert record.actual_findings == "No issues"

    def test_complete_from_scheduled_raises(self):
        record = self._scheduled_record()
        with pytest.raises(InvalidMaintenanceStatusTransitionError):
            record.complete()

    def test_cancel_from_scheduled(self):
        record = self._scheduled_record()
        record.cancel("Not needed")
        assert record.status == MaintenanceStatus.CANCELLED
        assert record.cancellation_reason == "Not needed"

    def test_cancel_from_in_progress(self):
        record = self._scheduled_record()
        record.start()
        record.cancel("Blocked by vendor")
        assert record.status == MaintenanceStatus.CANCELLED

    def test_cancel_requires_reason(self):
        record = self._scheduled_record()
        with pytest.raises(ValueError, match="Cancellation reason"):
            record.cancel(" ")

    def test_skip_from_scheduled(self):
        record = self._scheduled_record()
        record.skip("Asset unavailable")
        assert record.status == MaintenanceStatus.SKIPPED
        assert record.skip_reason == "Asset unavailable"

    def test_skip_requires_reason(self):
        record = self._scheduled_record()
        with pytest.raises(ValueError, match="Skip reason"):
            record.skip("")

    def test_skip_from_in_progress_raises(self):
        record = self._scheduled_record()
        record.start()
        with pytest.raises(InvalidMaintenanceStatusTransitionError):
            record.skip("Too late")


class TestMaintenanceRecordUpdate:

    def test_update_scheduled_fields(self):
        scheduled_at = datetime(2026, 3, 2, 9, 0, tzinfo=UTC)
        record = MaintenanceRecord.create(
            company_id="c1",
            asset_id="a1",
            title="Old",
        )
        record.update_scheduled(
            title="New",
            description="Updated",
            priority=MaintenancePriority.CRITICAL,
            checklist_items=["A", "B"],
            scheduled_at=scheduled_at,
        )
        assert record.title == "New"
        assert record.description == "Updated"
        assert record.priority == MaintenancePriority.CRITICAL
        assert record.checklist_items == ["A", "B"]
        assert record.scheduled_at == scheduled_at

    def test_update_scheduled_rejects_non_scheduled(self):
        record = MaintenanceRecord.create(
            company_id="c1",
            asset_id="a1",
            title="Any",
            technician_id="tech1",
        )
        record.start()
        with pytest.raises(ValueError, match="Only SCHEDULED"):
            record.update_scheduled(title="Not allowed")


class TestMaintenanceRecordFlags:

    def test_mark_reminder_sent(self):
        record = MaintenanceRecord.create(
            company_id="c1",
            asset_id="a1",
            title="Filter change",
        )
        assert record.reminder_48h_sent is False
        record.mark_reminder_sent()
        assert record.reminder_48h_sent is True

    def test_mark_overdue_alert_sent(self):
        record = MaintenanceRecord.create(
            company_id="c1",
            asset_id="a1",
            title="Filter change",
        )
        assert record.overdue_alert_sent is False
        record.mark_overdue_alert_sent()
        assert record.overdue_alert_sent is True


class TestMaintenanceStatusProperties:

    def test_terminal_statuses(self):
        assert MaintenanceStatus.COMPLETED.is_terminal is True
        assert MaintenanceStatus.CANCELLED.is_terminal is True
        assert MaintenanceStatus.SKIPPED.is_terminal is True

    def test_non_terminal_statuses(self):
        assert MaintenanceStatus.SCHEDULED.is_terminal is False
        assert MaintenanceStatus.IN_PROGRESS.is_terminal is False
