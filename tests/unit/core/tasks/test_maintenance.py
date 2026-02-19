from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

from src.maintenance_bc.maintenance_record.domain.entities import (
    MaintenanceRecord,
)
from src.maintenance_bc.maintenance_record.domain.enums import (
    MaintenancePriority,
    RecurrenceFrequency,
)
from src.maintenance_bc.maintenance_template.domain.entities import (
    ChecklistItem,
    MaintenancePlan,
    MaintenanceTemplate,
)


def _make_record(
    scheduled_offset_hours: int,
    overdue: bool = False,
) -> MaintenanceRecord:
    now = datetime.now(UTC)
    scheduled_at = now - timedelta(hours=scheduled_offset_hours) if overdue else now + timedelta(hours=scheduled_offset_hours)
    return MaintenanceRecord.create(
        company_id="comp1",
        asset_id="asset1",
        title="Check battery",
        technician_id="tech1",
        scheduled_at=scheduled_at,
    )


class TestMaintenanceTasks:

    @patch("src.notification_bc.notification.infrastructure.repository.NotificationRepository")
    @patch("src.maintenance_bc.maintenance_record.infrastructure.repository.MaintenanceRecordRepository")
    @patch("core.database.SessionLocal")
    def test_send_maintenance_reminders(
        self,
        MockSession,
        MockRecordRepo,
        MockNotifRepo,
    ):
        from core.tasks.maintenance import send_maintenance_reminders

        session = MagicMock()
        session.execute.return_value.scalars.return_value.all.return_value = ["comp1"]
        MockSession.return_value = session

        record = _make_record(scheduled_offset_hours=24)
        record_repo = MagicMock()
        record_repo.find_due_within_hours.return_value = [record]
        MockRecordRepo.return_value = record_repo

        notif_repo = MagicMock()
        MockNotifRepo.return_value = notif_repo

        result = send_maintenance_reminders()

        assert result == 1
        notif_repo.save.assert_called_once()
        record_repo.save.assert_called_once()
        session.commit.assert_called_once()

    @patch("src.notification_bc.notification.infrastructure.repository.NotificationRepository")
    @patch("src.maintenance_bc.maintenance_record.infrastructure.repository.MaintenanceRecordRepository")
    @patch("core.database.SessionLocal")
    def test_check_overdue_maintenance(
        self,
        MockSession,
        MockRecordRepo,
        MockNotifRepo,
    ):
        from core.tasks.maintenance import check_overdue_maintenance

        session = MagicMock()
        session.execute.return_value.scalars.return_value.all.return_value = ["comp1"]
        MockSession.return_value = session

        record = _make_record(scheduled_offset_hours=1, overdue=True)
        record_repo = MagicMock()
        record_repo.find_overdue.return_value = [record]
        MockRecordRepo.return_value = record_repo

        notif_repo = MagicMock()
        MockNotifRepo.return_value = notif_repo

        result = check_overdue_maintenance()

        assert result == 1
        notif_repo.save.assert_called_once()
        record_repo.save.assert_called_once()
        session.commit.assert_called_once()

    @patch("src.maintenance_bc.maintenance_record.infrastructure.repository.MaintenanceRecordRepository")
    @patch("src.maintenance_bc.maintenance_template.infrastructure.repository.MaintenanceTemplateRepository")
    @patch("src.maintenance_bc.maintenance_template.infrastructure.repository.MaintenancePlanRepository")
    @patch("core.database.SessionLocal")
    def test_generate_recurring_maintenance(
        self,
        MockSession,
        MockPlanRepo,
        MockTemplateRepo,
        MockRecordRepo,
    ):
        from core.tasks.maintenance import generate_recurring_maintenance

        session = MagicMock()
        session.execute.return_value.scalars.return_value.all.return_value = ["comp1"]
        MockSession.return_value = session

        due_plan = MaintenancePlan.create(
            company_id="comp1",
            template_id="tpl1",
            asset_id="asset1",
            next_due_at=datetime.now(UTC),
        )
        plan_repo = MagicMock()
        plan_repo.find_due_plans.return_value = [due_plan]
        MockPlanRepo.return_value = plan_repo

        template = MaintenanceTemplate.create(
            company_id="comp1",
            name="Monthly check",
            default_priority=MaintenancePriority.HIGH,
            recurrence_frequency=RecurrenceFrequency.MONTHLY,
            recurrence_interval=1,
            checklist_items=[ChecklistItem.create("Inspect")],
            id="tpl1",
        )
        template_repo = MagicMock()
        template_repo.find_by_ids.return_value = {"tpl1": template}
        MockTemplateRepo.return_value = template_repo

        record_repo = MagicMock()
        MockRecordRepo.return_value = record_repo

        result = generate_recurring_maintenance()

        assert result == 1
        record_repo.save.assert_called_once()
        plan_repo.save.assert_called_once()
        session.commit.assert_called_once()
