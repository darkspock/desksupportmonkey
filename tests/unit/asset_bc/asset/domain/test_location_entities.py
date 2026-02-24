import pytest

from src.asset_bc.asset.domain.entities import Asset, AssetLocation
from src.asset_bc.asset.domain.enums import AssetStatus, AssetType


class TestAssetLocation:
    def test_create_valid(self):
        loc = AssetLocation.create(
            company_id="comp1",
            name="Server Room",
        )
        assert loc.name == "Server Room"
        assert loc.company_id == "comp1"
        assert loc.is_system is False
        assert loc.system_key is None
        assert loc.in_use is True
        assert len(loc.id) == 26

    def test_create_system_location(self):
        loc = AssetLocation.create(
            company_id="comp1",
            name="Empleado",
            is_system=True,
            system_key="employee",
        )
        assert loc.is_system is True
        assert loc.system_key == "employee"

    def test_create_strips_whitespace(self):
        loc = AssetLocation.create(
            company_id="comp1",
            name="  Server Room  ",
        )
        assert loc.name == "Server Room"

    def test_create_empty_name_raises(self):
        with pytest.raises(ValueError, match="Location name is required"):
            AssetLocation.create(company_id="comp1", name="")

    def test_create_whitespace_only_name_raises(self):
        with pytest.raises(ValueError, match="Location name is required"):
            AssetLocation.create(company_id="comp1", name="   ")

    def test_create_system_without_key_raises(self):
        with pytest.raises(ValueError, match="system_key"):
            AssetLocation.create(
                company_id="comp1",
                name="System Loc",
                is_system=True,
            )

    def test_create_with_custom_id(self):
        loc = AssetLocation.create(
            company_id="comp1",
            name="Room 4",
            id="custom-id-123",
        )
        assert loc.id == "custom-id-123"

    def test_create_in_use_false(self):
        loc = AssetLocation.create(
            company_id="comp1",
            name="Old Room",
            in_use=False,
        )
        assert loc.in_use is False


class TestAssetMoveToLocation:
    def test_move_to_new_location(self):
        asset = Asset.create(
            company_id="comp1",
            type=AssetType.LAPTOP,
            brand="Dell",
            model="X",
            serial_number="SN1",
        )
        asset.location_id = "loc-old"
        changes = asset.move_to("loc-new")
        assert changes == {"old_location_id": "loc-old", "new_location_id": "loc-new"}
        assert asset.location_id == "loc-new"

    def test_move_to_same_location_noop(self):
        asset = Asset.create(
            company_id="comp1",
            type=AssetType.LAPTOP,
            brand="Dell",
            model="X",
            serial_number="SN1",
        )
        asset.location_id = "loc-a"
        changes = asset.move_to("loc-a")
        assert changes == {}
        assert asset.location_id == "loc-a"

    def test_move_from_none(self):
        asset = Asset.create(
            company_id="comp1",
            type=AssetType.LAPTOP,
            brand="Dell",
            model="X",
            serial_number="SN1",
        )
        assert asset.location_id is None
        changes = asset.move_to("loc-new")
        assert changes == {"old_location_id": None, "new_location_id": "loc-new"}
        assert asset.location_id == "loc-new"

    def test_decommission_clears_location(self):
        asset = Asset.create(
            company_id="comp1",
            type=AssetType.LAPTOP,
            brand="Dell",
            model="X",
            serial_number="SN1",
        )
        asset.location_id = "loc-warehouse"
        asset.change_status(AssetStatus.DECOMMISSIONED)
        assert asset.location_id is None
