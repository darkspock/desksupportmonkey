from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from src.maintenance_bc.maintenance_record.application.queries.get_maintenance_record import (
    GetMaintenanceRecordQuery,
    GetMaintenanceRecordQueryHandler,
    MaintenanceRecordNotFoundError,
)
from src.maintenance_bc.maintenance_record.application.queries.list_maintenance_records import (
    ListMaintenanceRecordsQuery,
    ListMaintenanceRecordsQueryHandler,
)
from src.maintenance_bc.maintenance_record.application.queries.maintenance_dashboard import (
    MaintenanceDashboardQuery,
    MaintenanceDashboardQueryHandler,
)
from src.maintenance_bc.maintenance_record.application.queries.my_maintenance import (
    MyMaintenanceQuery,
    MyMaintenanceQueryHandler,
)
from src.maintenance_bc.maintenance_record.domain.entities import (
    MaintenanceRecord,
)


def _record() -> MaintenanceRecord:
    return MaintenanceRecord.create(
        company_id="comp1",
        asset_id="asset1",
        title="Battery check",
        technician_id="tech1",
        scheduled_at=datetime(2026, 4, 1, 8, 0, tzinfo=UTC),
    )


class TestGetMaintenanceRecord:
    def test_get_returns_record(self):
        repo = MagicMock()
        repo.find_by_id.return_value = _record()
        handler = GetMaintenanceRecordQueryHandler(record_repo=repo)

        record = handler.handle(
            GetMaintenanceRecordQuery(
                record_id="m1",
                company_id="comp1",
            )
        )

        assert record.asset_id == "asset1"

    def test_get_not_found_raises(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None
        handler = GetMaintenanceRecordQueryHandler(record_repo=repo)

        with pytest.raises(MaintenanceRecordNotFoundError):
            handler.handle(GetMaintenanceRecordQuery(record_id="x", company_id="comp1"))


class TestListMaintenanceRecords:
    def test_list_with_filters(self):
        repo = MagicMock()
        repo.find_all.return_value = ([_record()], 1)
        handler = ListMaintenanceRecordsQueryHandler(record_repo=repo)

        items, total = handler.handle(
            ListMaintenanceRecordsQuery(
                company_id="comp1",
                status="SCHEDULED",
                technician_id="tech1",
            )
        )

        assert len(items) == 1
        assert total == 1


class TestMaintenanceDashboard:
    def test_dashboard_summary(self):
        repo = MagicMock()
        repo.count_dashboard.return_value = {
            "scheduled": 2,
            "overdue": 1,
            "in_progress": 3,
            "completed_30d": 5,
        }
        handler = MaintenanceDashboardQueryHandler(record_repo=repo)

        summary = handler.handle(
            MaintenanceDashboardQuery(company_id="comp1")
        )

        assert summary.scheduled == 2
        assert summary.overdue == 1
        assert summary.in_progress == 3
        assert summary.completed_30d == 5


class TestMyMaintenance:
    def test_my_queue(self):
        repo = MagicMock()
        repo.find_my_queue.return_value = ([_record()], 1)
        handler = MyMaintenanceQueryHandler(record_repo=repo)

        items, total = handler.handle(
            MyMaintenanceQuery(
                company_id="comp1",
                technician_id="tech1",
            )
        )

        assert len(items) == 1
        assert total == 1
        repo.find_my_queue.assert_called_once_with(
            company_id="comp1",
            technician_id="tech1",
            page=1,
            page_size=20,
        )
