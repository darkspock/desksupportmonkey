from unittest.mock import MagicMock, call

import pytest

from src.asset_bc.asset.application.commands.import_assets import (
    ImportAssetsCommand,
    ImportAssetsCommandHandler,
    InvalidCSVError,
)
from src.asset_bc.asset.domain.entities import Asset
from src.asset_bc.asset.domain.enums import AssetType


def _make_handler(repo=None):
    if repo is None:
        repo = MagicMock()
        repo.find_by_serial_number.return_value = None
        repo.save.side_effect = lambda a: a
    return ImportAssetsCommandHandler(asset_repo=repo), repo


def _csv(rows: list[str]) -> str:
    header = "type,brand,model,serial_number,purchase_date,warranty_expiration,notes"
    return "\n".join([header] + rows)


class TestImportAssetsCommand:
    def test_success_all_valid(self):
        handler, repo = _make_handler()
        csv_content = _csv([
            "laptop,Dell,Latitude 5520,SN001,2024-01-15,2027-01-15,Good condition",
            "monitor,LG,27UK850,SN002,,,"
        ])

        result = handler.handle(
            ImportAssetsCommand(company_id="comp1", performed_by="user1", csv_content=csv_content)
        )

        assert result.total == 2
        assert result.successful == 2
        assert result.failed == []
        assert repo.save.call_count == 2
        assert repo.save_event.call_count == 2

    def test_partial_some_rows_fail(self):
        handler, repo = _make_handler()
        csv_content = _csv([
            "laptop,Dell,Latitude,SN001,,,",
            "invalid_type,Dell,Latitude,SN002,,,",
            "laptop,Dell,Latitude,SN003,,,",
        ])

        result = handler.handle(
            ImportAssetsCommand(company_id="comp1", performed_by="user1", csv_content=csv_content)
        )

        assert result.total == 3
        assert result.successful == 2
        assert len(result.failed) == 1
        assert result.failed[0].row == 3
        assert "Invalid type" in result.failed[0].error

    def test_duplicate_serial_in_csv(self):
        handler, repo = _make_handler()
        csv_content = _csv([
            "laptop,Dell,Latitude,SN001,,,",
            "laptop,Dell,Latitude,SN001,,,",
        ])

        result = handler.handle(
            ImportAssetsCommand(company_id="comp1", performed_by="user1", csv_content=csv_content)
        )

        assert result.successful == 1
        assert len(result.failed) == 1
        assert "Duplicate serial" in result.failed[0].error

    def test_duplicate_serial_in_db(self):
        repo = MagicMock()
        repo.find_by_serial_number.side_effect = lambda sn, cid: (
            MagicMock() if sn == "SN001" else None
        )
        repo.save.side_effect = lambda a: a
        handler = ImportAssetsCommandHandler(asset_repo=repo)

        csv_content = _csv([
            "laptop,Dell,Latitude,SN001,,,",
            "laptop,Dell,Latitude,SN002,,,",
        ])

        result = handler.handle(
            ImportAssetsCommand(company_id="comp1", performed_by="user1", csv_content=csv_content)
        )

        assert result.successful == 1
        assert len(result.failed) == 1
        assert "already exists" in result.failed[0].error

    def test_missing_required_fields(self):
        handler, repo = _make_handler()
        csv_content = _csv([
            "laptop,,Latitude,SN001,,,",
            "laptop,Dell,,SN002,,,",
            "laptop,Dell,Latitude,,,,",
        ])

        result = handler.handle(
            ImportAssetsCommand(company_id="comp1", performed_by="user1", csv_content=csv_content)
        )

        assert result.total == 3
        assert result.successful == 0
        assert len(result.failed) == 3
        assert "brand is required" in result.failed[0].error
        assert "model is required" in result.failed[1].error
        assert "serial_number is required" in result.failed[2].error

    def test_invalid_type_enum(self):
        handler, repo = _make_handler()
        csv_content = _csv(["printer,HP,LaserJet,SN001,,,"])

        result = handler.handle(
            ImportAssetsCommand(company_id="comp1", performed_by="user1", csv_content=csv_content)
        )

        assert result.successful == 0
        assert len(result.failed) == 1
        assert "Invalid type" in result.failed[0].error

    def test_invalid_date_format(self):
        handler, repo = _make_handler()
        csv_content = _csv(["laptop,Dell,Latitude,SN001,not-a-date,,"])

        result = handler.handle(
            ImportAssetsCommand(company_id="comp1", performed_by="user1", csv_content=csv_content)
        )

        assert result.successful == 0
        assert len(result.failed) == 1
        assert "Invalid date" in result.failed[0].error

    def test_empty_csv_raises(self):
        handler, repo = _make_handler()

        with pytest.raises(InvalidCSVError, match="empty"):
            handler.handle(
                ImportAssetsCommand(company_id="comp1", performed_by="user1", csv_content="")
            )

    def test_missing_required_columns_raises(self):
        handler, repo = _make_handler()
        csv_content = "brand,model\nDell,Latitude"

        with pytest.raises(InvalidCSVError, match="Missing required columns"):
            handler.handle(
                ImportAssetsCommand(company_id="comp1", performed_by="user1", csv_content=csv_content)
            )

    def test_created_event_has_csv_import_source(self):
        handler, repo = _make_handler()
        csv_content = _csv(["laptop,Dell,Latitude,SN001,,,"])

        handler.handle(
            ImportAssetsCommand(company_id="comp1", performed_by="user1", csv_content=csv_content)
        )

        event = repo.save_event.call_args[0][0]
        assert event.event_type == "created"
        assert event.data == {"source": "csv_import"}
        assert event.performed_by == "user1"
