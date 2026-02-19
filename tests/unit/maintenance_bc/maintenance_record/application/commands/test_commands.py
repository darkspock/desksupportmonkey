from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from src.maintenance_bc.maintenance_record.application.commands.assign_maintenance_record import (
    AssignMaintenanceRecordCommand,
    AssignMaintenanceRecordCommandHandler,
)
from src.maintenance_bc.maintenance_record.application.commands.cancel_maintenance import (
    CancelMaintenanceCommand,
    CancelMaintenanceCommandHandler,
)
from src.maintenance_bc.maintenance_record.application.commands.complete_maintenance import (
    CompleteMaintenanceCommand,
    CompleteMaintenanceCommandHandler,
)
from src.maintenance_bc.maintenance_record.application.commands.create_maintenance_record import (
    AssetNotFoundError,
    CreateMaintenanceRecordCommand,
    CreateMaintenanceRecordCommandHandler,
    TechnicianNotFoundError,
)
from src.maintenance_bc.maintenance_record.application.commands.skip_maintenance import (
    SkipMaintenanceCommand,
    SkipMaintenanceCommandHandler,
)
from src.maintenance_bc.maintenance_record.application.commands.start_maintenance import (
    StartMaintenanceCommand,
    StartMaintenanceCommandHandler,
)
from src.maintenance_bc.maintenance_record.application.commands.update_maintenance_record import (
    UpdateMaintenanceRecordCommand,
    UpdateMaintenanceRecordCommandHandler,
)
from src.maintenance_bc.maintenance_record.domain.entities import (
    MaintenanceRecord,
)
from src.maintenance_bc.maintenance_record.domain.enums import (
    MaintenancePriority,
)


def _record(**overrides) -> MaintenanceRecord:
    defaults = dict(
        company_id="comp1",
        asset_id="asset1",
        title="Battery check",
        priority=MaintenancePriority.MEDIUM,
        technician_id="tech1",
    )
    defaults.update(overrides)
    return MaintenanceRecord.create(**defaults)


class TestCreateMaintenanceRecordCommand:
    def test_create_saves_record(self):
        record_repo = MagicMock()
        asset_lookup = MagicMock()
        user_lookup = MagicMock()
        asset_lookup.exists.return_value = True
        handler = CreateMaintenanceRecordCommandHandler(
            record_repo=record_repo,
            asset_lookup=asset_lookup,
            user_lookup=user_lookup,
        )

        handler.handle(
            CreateMaintenanceRecordCommand(
                record_id="m1",
                company_id="comp1",
                asset_id="asset1",
                title="Battery check",
                created_by="u1",
                priority="HIGH",
            )
        )

        record_repo.save.assert_called_once()
        saved = record_repo.save.call_args[0][0]
        assert saved.id == "m1"
        assert saved.priority == MaintenancePriority.HIGH

    def test_create_raises_when_asset_missing(self):
        record_repo = MagicMock()
        asset_lookup = MagicMock()
        user_lookup = MagicMock()
        asset_lookup.exists.return_value = False
        handler = CreateMaintenanceRecordCommandHandler(
            record_repo=record_repo,
            asset_lookup=asset_lookup,
            user_lookup=user_lookup,
        )

        with pytest.raises(AssetNotFoundError):
            handler.handle(
                CreateMaintenanceRecordCommand(
                    record_id="m1",
                    company_id="comp1",
                    asset_id="asset1",
                    title="Battery check",
                    created_by="u1",
                )
            )

    def test_create_raises_when_technician_not_found(self):
        record_repo = MagicMock()
        asset_lookup = MagicMock()
        user_lookup = MagicMock()
        asset_lookup.exists.return_value = True
        user_lookup.find_by_id_and_company.return_value = None
        handler = CreateMaintenanceRecordCommandHandler(
            record_repo=record_repo,
            asset_lookup=asset_lookup,
            user_lookup=user_lookup,
        )

        with pytest.raises(TechnicianNotFoundError):
            handler.handle(
                CreateMaintenanceRecordCommand(
                    record_id="m1",
                    company_id="comp1",
                    asset_id="asset1",
                    title="Battery check",
                    created_by="u1",
                    technician_id="invalid_id",
                )
            )


class TestLifecycleCommands:
    def test_assign(self):
        repo = MagicMock()
        user_lookup = MagicMock()
        user_lookup.find_by_id_and_company.return_value = MagicMock(is_active=True)
        record = _record()
        repo.find_by_id.return_value = record
        handler = AssignMaintenanceRecordCommandHandler(
            record_repo=repo,
            user_lookup=user_lookup,
        )

        handler.handle(
            AssignMaintenanceRecordCommand(
                record_id=record.id,
                company_id=record.company_id,
                technician_id="tech2",
            )
        )

        assert record.technician_id == "tech2"
        repo.save.assert_called_once_with(record)

    def test_start(self):
        repo = MagicMock()
        record = _record()
        repo.find_by_id.return_value = record
        handler = StartMaintenanceCommandHandler(record_repo=repo)

        handler.handle(
            StartMaintenanceCommand(
                record_id=record.id,
                company_id=record.company_id,
            )
        )

        assert record.started_at is not None
        repo.save.assert_called_once_with(record)

    def test_complete(self):
        repo = MagicMock()
        record = _record()
        record.start()
        repo.find_by_id.return_value = record
        handler = CompleteMaintenanceCommandHandler(record_repo=repo)

        handler.handle(
            CompleteMaintenanceCommand(
                record_id=record.id,
                company_id=record.company_id,
                completion_notes="Done",
                actual_findings="All good",
            )
        )

        assert record.completed_at is not None
        assert record.completion_notes == "Done"
        repo.save.assert_called_once_with(record)

    def test_cancel(self):
        repo = MagicMock()
        record = _record()
        repo.find_by_id.return_value = record
        handler = CancelMaintenanceCommandHandler(record_repo=repo)

        handler.handle(
            CancelMaintenanceCommand(
                record_id=record.id,
                company_id=record.company_id,
                reason="Not needed",
            )
        )

        assert record.cancellation_reason == "Not needed"
        repo.save.assert_called_once_with(record)

    def test_skip(self):
        repo = MagicMock()
        record = _record()
        repo.find_by_id.return_value = record
        handler = SkipMaintenanceCommandHandler(record_repo=repo)

        handler.handle(
            SkipMaintenanceCommand(
                record_id=record.id,
                company_id=record.company_id,
                reason="Asset unavailable",
            )
        )

        assert record.skip_reason == "Asset unavailable"
        repo.save.assert_called_once_with(record)


class TestUpdateCommand:
    def test_update_scheduled_fields(self):
        repo = MagicMock()
        record = _record(title="Old title")
        repo.find_by_id.return_value = record
        handler = UpdateMaintenanceRecordCommandHandler(record_repo=repo)

        handler.handle(
            UpdateMaintenanceRecordCommand(
                record_id=record.id,
                company_id=record.company_id,
                title="New title",
                priority="CRITICAL",
                description="Updated",
                checklist_items=["A", "B"],
                scheduled_at=datetime(2026, 4, 1, 10, 0, tzinfo=UTC),
            )
        )

        assert record.title == "New title"
        assert record.priority == MaintenancePriority.CRITICAL
        assert record.description == "Updated"
        assert record.checklist_items == ["A", "B"]
        repo.save.assert_called_once_with(record)

    def test_update_non_scheduled_raises(self):
        repo = MagicMock()
        record = _record()
        record.start()
        repo.find_by_id.return_value = record
        handler = UpdateMaintenanceRecordCommandHandler(record_repo=repo)

        with pytest.raises(ValueError, match="Only SCHEDULED"):
            handler.handle(
                UpdateMaintenanceRecordCommand(
                    record_id=record.id,
                    company_id=record.company_id,
                    title="Not allowed",
                )
            )
