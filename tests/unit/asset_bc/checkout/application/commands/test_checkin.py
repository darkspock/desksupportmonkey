from unittest.mock import MagicMock, call

import pytest

from src.asset_bc.asset.domain.entities import Asset
from src.asset_bc.asset.domain.enums import AssetStatus
from src.asset_bc.checkout.application.commands.checkin_asset import (
    AssetNotFoundError,
    CheckinAssetCommand,
    CheckinAssetCommandHandler,
)
from src.asset_bc.checkout.domain.entities import AssetCheckout
from src.asset_bc.checkout.domain.enums import AssetCondition
from src.asset_bc.checkout.domain.exceptions import NoActiveCheckoutError


def _make_asset(**overrides):
    defaults = dict(
        company_id="comp1", type="laptop",
        brand="Dell", model="Latitude", serial_number="SN001",
    )
    defaults.update(overrides)
    asset = Asset.create(**defaults)
    asset.assign(user_id="user1", department_id="dept1")
    return asset


def _make_checkout(**overrides):
    defaults = dict(
        company_id="comp1",
        asset_id="asset1",
        user_id="user1",
        checked_out_by="tech1",
        condition_out=AssetCondition.GOOD,
    )
    defaults.update(overrides)
    return AssetCheckout.create(**defaults)


def _make_command(**overrides):
    defaults = dict(
        asset_id="asset1",
        company_id="comp1",
        performed_by="tech1",
        condition_in="good",
    )
    defaults.update(overrides)
    return CheckinAssetCommand(**defaults)


class TestCheckinHappyPath:
    def test_checkin_marks_asset_in_repair(self):
        asset = _make_asset()
        checkout = _make_checkout(asset_id=asset.id)

        asset_repo = MagicMock()
        asset_repo.find_by_id.return_value = asset
        checkout_repo = MagicMock()
        checkout_repo.find_active_by_asset.return_value = checkout
        maintenance_creator = MagicMock()

        handler = CheckinAssetCommandHandler(
            asset_repo=asset_repo,
            checkout_repo=checkout_repo,
            maintenance_creator=maintenance_creator,
        )
        handler.handle(_make_command(asset_id=asset.id, condition_in="fair"))

        assert checkout.checked_in_at is not None
        assert asset.status == AssetStatus.IN_REPAIR
        assert asset.assigned_to is None
        asset_repo.save.assert_called_once()
        maintenance_creator.create.assert_called_once()

        # Maintenance record created via port
        call_kwargs = maintenance_creator.create.call_args
        assert "GDPR" in call_kwargs.kwargs.get("title", call_kwargs[1].get("title", ""))

    def test_checkin_links_maintenance_to_checkout(self):
        asset = _make_asset()
        checkout = _make_checkout(asset_id=asset.id)

        asset_repo = MagicMock()
        asset_repo.find_by_id.return_value = asset
        checkout_repo = MagicMock()
        checkout_repo.find_active_by_asset.return_value = checkout
        maintenance_creator = MagicMock()

        handler = CheckinAssetCommandHandler(
            asset_repo=asset_repo,
            checkout_repo=checkout_repo,
            maintenance_creator=maintenance_creator,
        )
        handler.handle(_make_command(asset_id=asset.id))

        # checkout_repo.save called to link maintenance_id
        assert checkout_repo.save.call_count == 1
        assert checkout.maintenance_id is not None

    def test_checkin_creates_event(self):
        asset = _make_asset()
        checkout = _make_checkout(asset_id=asset.id)

        asset_repo = MagicMock()
        asset_repo.find_by_id.return_value = asset
        checkout_repo = MagicMock()
        checkout_repo.find_active_by_asset.return_value = checkout
        maintenance_creator = MagicMock()

        handler = CheckinAssetCommandHandler(
            asset_repo=asset_repo,
            checkout_repo=checkout_repo,
            maintenance_creator=maintenance_creator,
        )
        handler.handle(_make_command(asset_id=asset.id))

        asset_repo.save_event.assert_called_once()
        event = asset_repo.save_event.call_args[0][0]
        assert event.event_type == "checked_in"

    def test_checkin_passes_source_type_to_maintenance(self):
        asset = _make_asset()
        checkout = _make_checkout(asset_id=asset.id)

        asset_repo = MagicMock()
        asset_repo.find_by_id.return_value = asset
        checkout_repo = MagicMock()
        checkout_repo.find_active_by_asset.return_value = checkout
        maintenance_creator = MagicMock()

        handler = CheckinAssetCommandHandler(
            asset_repo=asset_repo,
            checkout_repo=checkout_repo,
            maintenance_creator=maintenance_creator,
        )
        handler.handle(_make_command(asset_id=asset.id))

        maintenance_creator.create.assert_called_once()
        kwargs = maintenance_creator.create.call_args.kwargs
        assert kwargs["source_type"] == "checkout_gdpr"
        assert kwargs["priority"] == "HIGH"


class TestCheckinConditionToStatus:
    def test_unusable_sets_decommissioned(self):
        asset = _make_asset()
        checkout = _make_checkout(asset_id=asset.id)

        asset_repo = MagicMock()
        asset_repo.find_by_id.return_value = asset
        checkout_repo = MagicMock()
        checkout_repo.find_active_by_asset.return_value = checkout
        maintenance_creator = MagicMock()

        handler = CheckinAssetCommandHandler(
            asset_repo=asset_repo,
            checkout_repo=checkout_repo,
            maintenance_creator=maintenance_creator,
        )
        handler.handle(_make_command(asset_id=asset.id, condition_in="unusable"))
        assert asset.status == AssetStatus.DECOMMISSIONED

    def test_good_sets_in_repair(self):
        asset = _make_asset()
        checkout = _make_checkout(asset_id=asset.id)

        asset_repo = MagicMock()
        asset_repo.find_by_id.return_value = asset
        checkout_repo = MagicMock()
        checkout_repo.find_active_by_asset.return_value = checkout
        maintenance_creator = MagicMock()

        handler = CheckinAssetCommandHandler(
            asset_repo=asset_repo,
            checkout_repo=checkout_repo,
            maintenance_creator=maintenance_creator,
        )
        handler.handle(_make_command(asset_id=asset.id, condition_in="good"))
        assert asset.status == AssetStatus.IN_REPAIR

    def test_damaged_sets_in_repair(self):
        asset = _make_asset()
        checkout = _make_checkout(asset_id=asset.id)

        asset_repo = MagicMock()
        asset_repo.find_by_id.return_value = asset
        checkout_repo = MagicMock()
        checkout_repo.find_active_by_asset.return_value = checkout
        maintenance_creator = MagicMock()

        handler = CheckinAssetCommandHandler(
            asset_repo=asset_repo,
            checkout_repo=checkout_repo,
            maintenance_creator=maintenance_creator,
        )
        handler.handle(_make_command(asset_id=asset.id, condition_in="damaged"))
        assert asset.status == AssetStatus.IN_REPAIR


class TestCheckinValidation:
    def test_asset_not_found_raises(self):
        asset_repo = MagicMock()
        asset_repo.find_by_id.return_value = None

        handler = CheckinAssetCommandHandler(
            asset_repo=asset_repo,
            checkout_repo=MagicMock(),
            maintenance_creator=MagicMock(),
        )
        with pytest.raises(AssetNotFoundError):
            handler.handle(_make_command())

    def test_no_active_checkout_raises(self):
        asset = _make_asset()
        asset_repo = MagicMock()
        asset_repo.find_by_id.return_value = asset
        checkout_repo = MagicMock()
        checkout_repo.find_active_by_asset.return_value = None

        handler = CheckinAssetCommandHandler(
            asset_repo=asset_repo,
            checkout_repo=checkout_repo,
            maintenance_creator=MagicMock(),
        )
        with pytest.raises(NoActiveCheckoutError):
            handler.handle(_make_command(asset_id=asset.id))
