from unittest.mock import MagicMock

import pytest

from src.asset_bc.asset.application.commands.create_location import (
    CreateLocationCommand,
    CreateLocationCommandHandler,
)
from src.asset_bc.asset.application.commands.update_location import (
    UpdateLocationCommand,
    UpdateLocationCommandHandler,
)
from src.asset_bc.asset.application.commands.delete_location import (
    DeleteLocationCommand,
    DeleteLocationCommandHandler,
)
from src.asset_bc.asset.application.commands.move_asset import (
    AssetDecommissionedError,
    AssetNotFoundError,
    MoveAssetCommand,
    MoveAssetCommandHandler,
)
from src.asset_bc.asset.domain.entities import Asset, AssetLocation
from src.asset_bc.asset.domain.enums import AssetStatus
from src.asset_bc.asset.domain.exceptions import (
    LocationHasAssetsError,
    LocationNameExistsError,
    LocationNotFoundError,
    SystemLocationError,
)


def _make_location(**overrides):
    defaults = dict(
        company_id="comp1",
        name="Server Room",
    )
    defaults.update(overrides)
    return AssetLocation.create(**defaults)


def _make_asset(**overrides):
    defaults = dict(
        company_id="comp1",
        type="laptop",
        brand="Dell",
        model="Latitude",
        serial_number="SN001",
    )
    defaults.update(overrides)
    return Asset.create(**defaults)


# ── CreateLocationCommand ──────────────────────────────────────────────


class TestCreateLocationCommand:
    def test_success(self):
        repo = MagicMock()
        repo.find_location_by_name.return_value = None
        handler = CreateLocationCommandHandler(asset_repo=repo)

        handler.handle(
            CreateLocationCommand(company_id="comp1", name="Room 4")
        )

        repo.save_location.assert_called_once()
        saved = repo.save_location.call_args[0][0]
        assert saved.name == "Room 4"
        assert saved.company_id == "comp1"
        assert saved.is_system is False

    def test_duplicate_name_raises(self):
        repo = MagicMock()
        repo.find_location_by_name.return_value = _make_location()
        handler = CreateLocationCommandHandler(asset_repo=repo)

        with pytest.raises(LocationNameExistsError):
            handler.handle(
                CreateLocationCommand(company_id="comp1", name="Server Room")
            )
        repo.save_location.assert_not_called()

    def test_in_use_defaults_true(self):
        repo = MagicMock()
        repo.find_location_by_name.return_value = None
        handler = CreateLocationCommandHandler(asset_repo=repo)

        handler.handle(
            CreateLocationCommand(company_id="comp1", name="New Room")
        )

        saved = repo.save_location.call_args[0][0]
        assert saved.in_use is True


# ── UpdateLocationCommand ──────────────────────────────────────────────


class TestUpdateLocationCommand:
    def test_success_update_name(self):
        loc = _make_location()
        repo = MagicMock()
        repo.find_location_by_id.return_value = loc
        repo.find_location_by_name.return_value = None
        handler = UpdateLocationCommandHandler(asset_repo=repo)

        handler.handle(
            UpdateLocationCommand(
                location_id=loc.id, company_id="comp1", name="New Name"
            )
        )

        repo.save_location.assert_called_once()
        assert loc.name == "New Name"

    def test_success_update_in_use(self):
        loc = _make_location()
        repo = MagicMock()
        repo.find_location_by_id.return_value = loc
        handler = UpdateLocationCommandHandler(asset_repo=repo)

        handler.handle(
            UpdateLocationCommand(
                location_id=loc.id, company_id="comp1", in_use=False
            )
        )

        repo.save_location.assert_called_once()
        assert loc.in_use is False

    def test_not_found_raises(self):
        repo = MagicMock()
        repo.find_location_by_id.return_value = None
        handler = UpdateLocationCommandHandler(asset_repo=repo)

        with pytest.raises(LocationNotFoundError):
            handler.handle(
                UpdateLocationCommand(
                    location_id="bad", company_id="comp1", name="X"
                )
            )

    def test_system_location_raises(self):
        loc = _make_location(is_system=True, system_key="employee")
        repo = MagicMock()
        repo.find_location_by_id.return_value = loc
        handler = UpdateLocationCommandHandler(asset_repo=repo)

        with pytest.raises(SystemLocationError):
            handler.handle(
                UpdateLocationCommand(
                    location_id=loc.id, company_id="comp1", name="Renamed"
                )
            )

    def test_duplicate_name_raises(self):
        loc = _make_location()
        other = _make_location(name="Other Room")
        repo = MagicMock()
        repo.find_location_by_id.return_value = loc
        repo.find_location_by_name.return_value = other
        handler = UpdateLocationCommandHandler(asset_repo=repo)

        with pytest.raises(LocationNameExistsError):
            handler.handle(
                UpdateLocationCommand(
                    location_id=loc.id, company_id="comp1", name="Other Room"
                )
            )


# ── DeleteLocationCommand ──────────────────────────────────────────────


class TestDeleteLocationCommand:
    def test_success(self):
        loc = _make_location()
        repo = MagicMock()
        repo.find_location_by_id.return_value = loc
        repo.count_assets_at_location.return_value = 0
        handler = DeleteLocationCommandHandler(asset_repo=repo)

        handler.handle(
            DeleteLocationCommand(location_id=loc.id, company_id="comp1")
        )

        repo.delete_location.assert_called_once_with(loc.id)

    def test_not_found_raises(self):
        repo = MagicMock()
        repo.find_location_by_id.return_value = None
        handler = DeleteLocationCommandHandler(asset_repo=repo)

        with pytest.raises(LocationNotFoundError):
            handler.handle(
                DeleteLocationCommand(location_id="bad", company_id="comp1")
            )

    def test_system_location_raises(self):
        loc = _make_location(is_system=True, system_key="main_warehouse")
        repo = MagicMock()
        repo.find_location_by_id.return_value = loc
        handler = DeleteLocationCommandHandler(asset_repo=repo)

        with pytest.raises(SystemLocationError):
            handler.handle(
                DeleteLocationCommand(location_id=loc.id, company_id="comp1")
            )

    def test_has_assets_raises(self):
        loc = _make_location()
        repo = MagicMock()
        repo.find_location_by_id.return_value = loc
        repo.count_assets_at_location.return_value = 3
        handler = DeleteLocationCommandHandler(asset_repo=repo)

        with pytest.raises(LocationHasAssetsError):
            handler.handle(
                DeleteLocationCommand(location_id=loc.id, company_id="comp1")
            )
        repo.delete_location.assert_not_called()


# ── MoveAssetCommand ───────────────────────────────────────────────────


class TestMoveAssetCommand:
    def test_success(self):
        asset = _make_asset()
        asset.location_id = "loc-old"
        old_loc = _make_location(name="Old Room")
        old_loc.id = "loc-old"
        new_loc = _make_location(name="New Room")
        new_loc.id = "loc-new"

        repo = MagicMock()
        repo.find_by_id.return_value = asset
        repo.find_location_by_id.side_effect = lambda lid, cid: (
            new_loc if lid == "loc-new" else old_loc if lid == "loc-old" else None
        )
        handler = MoveAssetCommandHandler(asset_repo=repo)

        handler.handle(
            MoveAssetCommand(
                asset_id=asset.id, company_id="comp1",
                location_id="loc-new", performed_by="user1",
            )
        )

        repo.save.assert_called_once()
        repo.save_event.assert_called_once()
        event = repo.save_event.call_args[0][0]
        assert event.event_type == "location_changed"
        assert event.data["new_location_name"] == "New Room"
        assert event.data["old_location_name"] == "Old Room"

    def test_asset_not_found_raises(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None
        handler = MoveAssetCommandHandler(asset_repo=repo)

        with pytest.raises(AssetNotFoundError):
            handler.handle(
                MoveAssetCommand(
                    asset_id="bad", company_id="comp1",
                    location_id="loc-1", performed_by="user1",
                )
            )

    def test_decommissioned_raises(self):
        asset = _make_asset()
        asset.status = AssetStatus.DECOMMISSIONED
        repo = MagicMock()
        repo.find_by_id.return_value = asset
        handler = MoveAssetCommandHandler(asset_repo=repo)

        with pytest.raises(AssetDecommissionedError):
            handler.handle(
                MoveAssetCommand(
                    asset_id=asset.id, company_id="comp1",
                    location_id="loc-1", performed_by="user1",
                )
            )

    def test_location_not_found_raises(self):
        asset = _make_asset()
        repo = MagicMock()
        repo.find_by_id.return_value = asset
        repo.find_location_by_id.return_value = None
        handler = MoveAssetCommandHandler(asset_repo=repo)

        with pytest.raises(LocationNotFoundError):
            handler.handle(
                MoveAssetCommand(
                    asset_id=asset.id, company_id="comp1",
                    location_id="bad-loc", performed_by="user1",
                )
            )

    def test_same_location_noop(self):
        asset = _make_asset()
        asset.location_id = "loc-same"
        loc = _make_location()
        loc.id = "loc-same"

        repo = MagicMock()
        repo.find_by_id.return_value = asset
        repo.find_location_by_id.return_value = loc
        handler = MoveAssetCommandHandler(asset_repo=repo)

        handler.handle(
            MoveAssetCommand(
                asset_id=asset.id, company_id="comp1",
                location_id="loc-same", performed_by="user1",
            )
        )

        repo.save.assert_not_called()
        repo.save_event.assert_not_called()

    def test_move_with_notes(self):
        asset = _make_asset()
        asset.location_id = "loc-old"
        old_loc = _make_location(name="Old")
        old_loc.id = "loc-old"
        new_loc = _make_location(name="New")
        new_loc.id = "loc-new"

        repo = MagicMock()
        repo.find_by_id.return_value = asset
        repo.find_location_by_id.side_effect = lambda lid, cid: (
            new_loc if lid == "loc-new" else old_loc if lid == "loc-old" else None
        )
        handler = MoveAssetCommandHandler(asset_repo=repo)

        handler.handle(
            MoveAssetCommand(
                asset_id=asset.id, company_id="comp1",
                location_id="loc-new", performed_by="user1",
                notes="Moved for maintenance",
            )
        )

        event = repo.save_event.call_args[0][0]
        assert event.data["notes"] == "Moved for maintenance"
