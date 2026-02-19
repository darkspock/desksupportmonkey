from datetime import date
from unittest.mock import MagicMock

import pytest

from src.asset_bc.asset.application.commands.create_asset import (
    CreateAssetCommand,
    CreateAssetCommandHandler,
    SerialNumberExistsError,
)
from src.asset_bc.asset.application.commands.update_asset import (
    AssetNotFoundError as UpdateNotFoundError,
    UpdateAssetCommand,
    UpdateAssetCommandHandler,
)
from src.asset_bc.asset.application.commands.change_asset_status import (
    AssetNotFoundError as StatusNotFoundError,
    ChangeAssetStatusCommand,
    ChangeAssetStatusCommandHandler,
)
from src.asset_bc.asset.domain.entities import Asset
from src.asset_bc.asset.domain.enums import AssetStatus, AssetType, InvalidStatusTransitionError


def _make_asset(**overrides):
    defaults = dict(
        company_id="comp1",
        type=AssetType.LAPTOP,
        brand="Dell",
        model="Latitude",
        serial_number="SN001",
    )
    defaults.update(overrides)
    return Asset.create(**defaults)


class TestCreateAssetCommand:
    def test_success(self):
        repo = MagicMock()
        repo.find_by_serial_number.return_value = None
        repo.save.side_effect = lambda a: a
        handler = CreateAssetCommandHandler(asset_repo=repo)

        handler.handle(
            CreateAssetCommand(
                company_id="comp1",
                type="laptop",
                brand="Dell",
                model="Latitude 5520",
                serial_number="SN001",
                performed_by="user1",
            )
        )

        repo.save.assert_called_once()
        repo.save_event.assert_called_once()

    def test_duplicate_serial_raises(self):
        repo = MagicMock()
        repo.find_by_serial_number.return_value = _make_asset()
        handler = CreateAssetCommandHandler(asset_repo=repo)

        with pytest.raises(SerialNumberExistsError):
            handler.handle(
                CreateAssetCommand(
                    company_id="comp1", type="laptop", brand="Dell",
                    model="X", serial_number="SN001", performed_by="user1",
                )
            )
        repo.save.assert_not_called()


class TestUpdateAssetCommand:
    def test_success_with_changes(self):
        asset = _make_asset()
        repo = MagicMock()
        repo.find_by_id.return_value = asset
        repo.save.side_effect = lambda a: a
        handler = UpdateAssetCommandHandler(asset_repo=repo)

        handler.handle(
            UpdateAssetCommand(
                asset_id=asset.id, company_id="comp1",
                performed_by="user1", brand="HP",
            )
        )

        repo.save.assert_called_once()
        repo.save_event.assert_called_once()

    def test_no_changes_no_event(self):
        asset = _make_asset()
        repo = MagicMock()
        repo.find_by_id.return_value = asset
        repo.save.side_effect = lambda a: a
        handler = UpdateAssetCommandHandler(asset_repo=repo)

        handler.handle(
            UpdateAssetCommand(
                asset_id=asset.id, company_id="comp1",
                performed_by="user1", brand="Dell",
            )
        )

        repo.save.assert_called_once()
        repo.save_event.assert_not_called()

    def test_not_found_raises(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None
        handler = UpdateAssetCommandHandler(asset_repo=repo)

        with pytest.raises(UpdateNotFoundError):
            handler.handle(
                UpdateAssetCommand(
                    asset_id="bad", company_id="comp1",
                    performed_by="user1", brand="HP",
                )
            )

    def test_creates_event_with_changed_fields(self):
        asset = _make_asset()
        repo = MagicMock()
        repo.find_by_id.return_value = asset
        repo.save.side_effect = lambda a: a
        handler = UpdateAssetCommandHandler(asset_repo=repo)

        handler.handle(
            UpdateAssetCommand(
                asset_id=asset.id, company_id="comp1",
                performed_by="user1", brand="HP", notes="new notes",
            )
        )

        event_call = repo.save_event.call_args[0][0]
        assert event_call.event_type == "updated"
        assert "brand" in event_call.data
        assert "notes" in event_call.data


class TestChangeAssetStatusCommand:
    def test_success(self):
        asset = _make_asset()
        repo = MagicMock()
        repo.find_by_id.return_value = asset
        repo.save.side_effect = lambda a: a
        handler = ChangeAssetStatusCommandHandler(asset_repo=repo)

        handler.handle(
            ChangeAssetStatusCommand(
                asset_id=asset.id, company_id="comp1",
                new_status="in_repair", performed_by="user1",
            )
        )

        repo.save.assert_called_once()
        repo.save_event.assert_called_once()

    def test_not_found_raises(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None
        handler = ChangeAssetStatusCommandHandler(asset_repo=repo)

        with pytest.raises(StatusNotFoundError):
            handler.handle(
                ChangeAssetStatusCommand(
                    asset_id="bad", company_id="comp1",
                    new_status="in_repair", performed_by="user1",
                )
            )

    def test_invalid_transition_raises(self):
        asset = _make_asset()
        repo = MagicMock()
        repo.find_by_id.return_value = asset
        handler = ChangeAssetStatusCommandHandler(asset_repo=repo)

        with pytest.raises(InvalidStatusTransitionError):
            handler.handle(
                ChangeAssetStatusCommand(
                    asset_id=asset.id, company_id="comp1",
                    new_status="assigned", performed_by="user1",
                )
            )

    def test_decommission_clears_assignment_and_creates_extra_event(self):
        asset = _make_asset()
        asset.assigned_to = "user99"
        asset.department_id = "dept1"
        asset.status = AssetStatus.ASSIGNED
        repo = MagicMock()
        repo.find_by_id.return_value = asset
        repo.save.side_effect = lambda a: a
        handler = ChangeAssetStatusCommandHandler(asset_repo=repo)

        handler.handle(
            ChangeAssetStatusCommand(
                asset_id=asset.id, company_id="comp1",
                new_status="decommissioned", performed_by="user1",
            )
        )

        repo.save.assert_called_once()
        assert repo.save_event.call_count == 2
        event_types = [call[0][0].event_type for call in repo.save_event.call_args_list]
        assert "status_changed" in event_types
        assert "unassigned" in event_types
