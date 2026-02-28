from datetime import date

import pytest

from src.asset_bc.asset.domain.entities import (
    Asset,
    AssetDecommissionedError,
    AssetEvent,
    InvalidAssignmentError,
)
from src.asset_bc.asset.domain.enums import AssetCriticality, AssetStatus, InvalidStatusTransitionError


class TestAsset:
    def test_create_valid(self):
        asset = Asset.create(
            company_id="comp1",
            type="laptop",
            brand="Dell",
            model="Latitude 5520",
            serial_number="SN123",
        )
        assert asset.brand == "Dell"
        assert asset.model == "Latitude 5520"
        assert asset.serial_number == "SN123"
        assert asset.type == "laptop"
        assert asset.status == AssetStatus.IN_STOCK
        assert asset.company_id == "comp1"
        assert len(asset.id) == 26
        assert asset.assigned_to is None
        assert asset.department_id is None

    def test_create_with_optional_fields(self):
        asset = Asset.create(
            company_id="comp1",
            type="monitor",
            brand="LG",
            model="27UK850",
            serial_number="MON456",
            purchase_date=date(2025, 1, 15),
            warranty_expiration=date(2028, 1, 15),
            notes="4K monitor",
        )
        assert asset.purchase_date == date(2025, 1, 15)
        assert asset.warranty_expiration == date(2028, 1, 15)
        assert asset.notes == "4K monitor"

    def test_create_strips_whitespace(self):
        asset = Asset.create(
            company_id="comp1",
            type="laptop",
            brand="  Dell  ",
            model="  Latitude  ",
            serial_number="  SN123  ",
            notes="  some notes  ",
        )
        assert asset.brand == "Dell"
        assert asset.model == "Latitude"
        assert asset.serial_number == "SN123"
        assert asset.notes == "some notes"

    def test_create_empty_brand_raises(self):
        with pytest.raises(ValueError, match="Brand is required"):
            Asset.create(
                company_id="comp1", type="laptop",
                brand="", model="X", serial_number="SN1",
            )

    def test_create_empty_model_raises(self):
        with pytest.raises(ValueError, match="Model is required"):
            Asset.create(
                company_id="comp1", type="laptop",
                brand="Dell", model="", serial_number="SN1",
            )

    def test_create_empty_serial_raises(self):
        with pytest.raises(ValueError, match="Serial number is required"):
            Asset.create(
                company_id="comp1", type="laptop",
                brand="Dell", model="X", serial_number="",
            )

    def test_update_fields(self):
        asset = Asset.create(
            company_id="comp1", type="laptop",
            brand="Dell", model="Old", serial_number="SN1",
        )
        changes = asset.update(brand="HP", model="New", notes="updated")
        assert asset.brand == "HP"
        assert asset.model == "New"
        assert asset.notes == "updated"
        assert "brand" in changes
        assert "model" in changes
        assert "notes" in changes

    def test_update_no_changes(self):
        asset = Asset.create(
            company_id="comp1", type="laptop",
            brand="Dell", model="X", serial_number="SN1",
        )
        changes = asset.update(brand="Dell")
        assert changes == {}

    def test_update_empty_brand_raises(self):
        asset = Asset.create(
            company_id="comp1", type="laptop",
            brand="Dell", model="X", serial_number="SN1",
        )
        with pytest.raises(ValueError, match="Brand cannot be empty"):
            asset.update(brand="  ")

    def test_change_status_valid_in_stock_to_in_repair(self):
        asset = Asset.create(
            company_id="comp1", type="laptop",
            brand="Dell", model="X", serial_number="SN1",
        )
        asset.change_status(AssetStatus.IN_REPAIR)
        assert asset.status == AssetStatus.IN_REPAIR

    def test_change_status_valid_in_repair_to_in_stock(self):
        asset = Asset.create(
            company_id="comp1", type="laptop",
            brand="Dell", model="X", serial_number="SN1",
        )
        asset.change_status(AssetStatus.IN_REPAIR)
        asset.change_status(AssetStatus.IN_STOCK)
        assert asset.status == AssetStatus.IN_STOCK

    def test_change_status_invalid_raises(self):
        asset = Asset.create(
            company_id="comp1", type="laptop",
            brand="Dell", model="X", serial_number="SN1",
        )
        with pytest.raises(InvalidStatusTransitionError):
            asset.change_status(AssetStatus.ASSIGNED)

    def test_change_status_decommissioned_is_terminal(self):
        asset = Asset.create(
            company_id="comp1", type="laptop",
            brand="Dell", model="X", serial_number="SN1",
        )
        asset.change_status(AssetStatus.DECOMMISSIONED)
        with pytest.raises(InvalidStatusTransitionError):
            asset.change_status(AssetStatus.IN_STOCK)

    def test_assign_success(self):
        asset = Asset.create(
            company_id="comp1", type="laptop",
            brand="Dell", model="X", serial_number="SN1",
        )
        asset.assign(user_id="user1", department_id="dept1")
        assert asset.status == AssetStatus.ASSIGNED
        assert asset.assigned_to == "user1"
        assert asset.department_id == "dept1"

    def test_assign_wrong_status_raises(self):
        asset = Asset.create(
            company_id="comp1", type="laptop",
            brand="Dell", model="X", serial_number="SN1",
        )
        asset.change_status(AssetStatus.IN_REPAIR)
        with pytest.raises(InvalidAssignmentError, match="must be in stock"):
            asset.assign(user_id="user1")

    def test_unassign_success(self):
        asset = Asset.create(
            company_id="comp1", type="laptop",
            brand="Dell", model="X", serial_number="SN1",
        )
        asset.assign(user_id="user1", department_id="dept1")
        asset.unassign()
        assert asset.status == AssetStatus.IN_STOCK
        assert asset.assigned_to is None
        assert asset.department_id is None

    def test_unassign_not_assigned_raises(self):
        asset = Asset.create(
            company_id="comp1", type="laptop",
            brand="Dell", model="X", serial_number="SN1",
        )
        with pytest.raises(InvalidAssignmentError, match="not currently assigned"):
            asset.unassign()

    def test_decommission_clears_assigned_to(self):
        asset = Asset.create(
            company_id="comp1", type="laptop",
            brand="Dell", model="X", serial_number="SN1",
        )
        asset.assigned_to = "user1"
        asset.department_id = "dept1"
        asset.status = AssetStatus.ASSIGNED
        asset.change_status(AssetStatus.DECOMMISSIONED)
        assert asset.assigned_to is None
        assert asset.department_id is None
        assert asset.status == AssetStatus.DECOMMISSIONED


class TestSetCriticality:
    def _make_asset(self, **overrides):
        defaults = dict(
            company_id="comp1",
            type="laptop",
            brand="Dell",
            model="Latitude",
            serial_number="SN001",
        )
        defaults.update(overrides)
        return Asset.create(**defaults)

    def test_set_to_critical(self):
        asset = self._make_asset()
        changes = asset.set_criticality(AssetCriticality.CRITICAL)
        assert asset.criticality == AssetCriticality.CRITICAL
        assert changes == {"old": None, "new": "critical"}

    def test_set_to_high(self):
        asset = self._make_asset()
        changes = asset.set_criticality(AssetCriticality.HIGH)
        assert asset.criticality == AssetCriticality.HIGH
        assert changes == {"old": None, "new": "high"}

    def test_set_to_medium(self):
        asset = self._make_asset()
        changes = asset.set_criticality(AssetCriticality.MEDIUM)
        assert asset.criticality == AssetCriticality.MEDIUM
        assert changes == {"old": None, "new": "medium"}

    def test_set_to_low(self):
        asset = self._make_asset()
        changes = asset.set_criticality(AssetCriticality.LOW)
        assert asset.criticality == AssetCriticality.LOW
        assert changes == {"old": None, "new": "low"}

    def test_clear_to_none(self):
        asset = self._make_asset()
        asset.criticality = AssetCriticality.HIGH
        changes = asset.set_criticality(None)
        assert asset.criticality is None
        assert changes == {"old": "high", "new": None}

    def test_same_value_returns_empty(self):
        asset = self._make_asset()
        asset.criticality = AssetCriticality.MEDIUM
        changes = asset.set_criticality(AssetCriticality.MEDIUM)
        assert changes == {}
        assert asset.criticality == AssetCriticality.MEDIUM

    def test_decommissioned_raises(self):
        asset = self._make_asset()
        asset.status = AssetStatus.DECOMMISSIONED
        with pytest.raises(AssetDecommissionedError, match="Cannot set criticality"):
            asset.set_criticality(AssetCriticality.CRITICAL)


class TestUpdateBia:
    def _make_asset(self, **overrides):
        defaults = dict(
            company_id="comp1",
            type="laptop",
            brand="Dell",
            model="Latitude",
            serial_number="SN001",
        )
        defaults.update(overrides)
        return Asset.create(**defaults)

    def test_valid_bia_update(self):
        asset = self._make_asset()
        changes = asset.update_bia(
            impact_score=5,
            rto_minutes=60,
            rpo_minutes=30,
            justification="test",
            reviewed_by="user1",
        )
        assert asset.impact_score == 5
        assert asset.rto_minutes == 60
        assert asset.rpo_minutes == 30
        assert asset.bia_justification == "test"
        assert asset.bia_reviewed_by == "user1"
        assert asset.bia_reviewed_at is not None
        assert "impact_score" in changes
        assert "rto_minutes" in changes
        assert "rpo_minutes" in changes
        assert "bia_justification" in changes

    def test_impact_score_zero_raises(self):
        asset = self._make_asset()
        with pytest.raises(ValueError, match="impact_score must be between 1 and 10"):
            asset.update_bia(
                impact_score=0,
                rto_minutes=60,
                rpo_minutes=30,
                justification="test",
                reviewed_by="user1",
            )

    def test_impact_score_eleven_raises(self):
        asset = self._make_asset()
        with pytest.raises(ValueError, match="impact_score must be between 1 and 10"):
            asset.update_bia(
                impact_score=11,
                rto_minutes=60,
                rpo_minutes=30,
                justification="test",
                reviewed_by="user1",
            )

    def test_rto_minutes_zero_raises(self):
        asset = self._make_asset()
        with pytest.raises(ValueError, match="rto_minutes must be greater than 0"):
            asset.update_bia(
                impact_score=5,
                rto_minutes=0,
                rpo_minutes=30,
                justification="test",
                reviewed_by="user1",
            )

    def test_rto_minutes_negative_raises(self):
        asset = self._make_asset()
        with pytest.raises(ValueError, match="rto_minutes must be greater than 0"):
            asset.update_bia(
                impact_score=5,
                rto_minutes=-1,
                rpo_minutes=30,
                justification="test",
                reviewed_by="user1",
            )

    def test_rpo_minutes_negative_raises(self):
        asset = self._make_asset()
        with pytest.raises(ValueError, match="rpo_minutes must be 0 or greater"):
            asset.update_bia(
                impact_score=5,
                rto_minutes=60,
                rpo_minutes=-1,
                justification="test",
                reviewed_by="user1",
            )

    def test_decommissioned_raises(self):
        asset = self._make_asset()
        asset.status = AssetStatus.DECOMMISSIONED
        with pytest.raises(AssetDecommissionedError, match="Cannot update BIA"):
            asset.update_bia(
                impact_score=5,
                rto_minutes=60,
                rpo_minutes=30,
                justification="test",
                reviewed_by="user1",
            )


class TestAssetEvent:
    def test_create(self):
        event = AssetEvent.create(
            asset_id="asset1",
            event_type="created",
            data={"brand": "Dell"},
            performed_by="user1",
        )
        assert event.asset_id == "asset1"
        assert event.event_type == "created"
        assert event.data == {"brand": "Dell"}
        assert event.performed_by == "user1"
        assert len(event.id) == 26
