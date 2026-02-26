from unittest.mock import MagicMock

import pytest

from src.asset_bc.asset.domain.entities import Asset
from src.asset_bc.asset.domain.enums import AssetStatus
from src.asset_bc.checkout.application.commands.cancel_checkout import (
    AssetNotFoundError,
    CancelCheckoutCommand,
    CancelCheckoutCommandHandler,
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
    return Asset.create(**defaults)


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
        reason="Changed mind",
    )
    defaults.update(overrides)
    return CancelCheckoutCommand(**defaults)


class TestCancelCheckoutHappyPath:
    def test_cancel_closes_checkout(self):
        asset = _make_asset()
        asset.assign(user_id="user1", department_id="dept1")
        checkout = _make_checkout(asset_id=asset.id, auto_assigned=False)

        asset_repo = MagicMock()
        asset_repo.find_by_id.return_value = asset
        checkout_repo = MagicMock()
        checkout_repo.find_active_by_asset.return_value = checkout

        handler = CancelCheckoutCommandHandler(
            asset_repo=asset_repo, checkout_repo=checkout_repo,
        )
        handler.handle(_make_command(asset_id=asset.id))

        assert checkout.is_cancelled is True
        checkout_repo.save.assert_called_once()
        asset_repo.save_event.assert_called_once()
        event = asset_repo.save_event.call_args[0][0]
        assert event.event_type == "checkout_cancelled"

    def test_cancel_with_reason(self):
        asset = _make_asset()
        asset.assign(user_id="user1", department_id="dept1")
        checkout = _make_checkout(asset_id=asset.id)

        asset_repo = MagicMock()
        asset_repo.find_by_id.return_value = asset
        checkout_repo = MagicMock()
        checkout_repo.find_active_by_asset.return_value = checkout

        handler = CancelCheckoutCommandHandler(
            asset_repo=asset_repo, checkout_repo=checkout_repo,
        )
        handler.handle(_make_command(asset_id=asset.id, reason="Wrong asset"))
        assert checkout.cancel_reason == "Wrong asset"


class TestCancelAutoAssigned:
    def test_reverts_asset_to_in_stock(self):
        asset = _make_asset()
        asset.assign(user_id="user1", department_id="dept1")
        checkout = _make_checkout(asset_id=asset.id, auto_assigned=True)

        asset_repo = MagicMock()
        asset_repo.find_by_id.return_value = asset
        checkout_repo = MagicMock()
        checkout_repo.find_active_by_asset.return_value = checkout

        handler = CancelCheckoutCommandHandler(
            asset_repo=asset_repo, checkout_repo=checkout_repo,
        )
        handler.handle(_make_command(asset_id=asset.id))

        assert asset.status == AssetStatus.IN_STOCK
        assert asset.assigned_to is None
        assert asset.department_id is None
        asset_repo.save.assert_called_once()

    def test_not_auto_assigned_keeps_asset_assigned(self):
        asset = _make_asset()
        asset.assign(user_id="user1", department_id="dept1")
        checkout = _make_checkout(asset_id=asset.id, auto_assigned=False)

        asset_repo = MagicMock()
        asset_repo.find_by_id.return_value = asset
        checkout_repo = MagicMock()
        checkout_repo.find_active_by_asset.return_value = checkout

        handler = CancelCheckoutCommandHandler(
            asset_repo=asset_repo, checkout_repo=checkout_repo,
        )
        handler.handle(_make_command(asset_id=asset.id))

        assert asset.status == AssetStatus.ASSIGNED
        assert asset.assigned_to == "user1"
        asset_repo.save.assert_not_called()

    def test_event_data_includes_auto_assigned_reverted(self):
        asset = _make_asset()
        asset.assign(user_id="user1", department_id="dept1")
        checkout = _make_checkout(asset_id=asset.id, auto_assigned=True)

        asset_repo = MagicMock()
        asset_repo.find_by_id.return_value = asset
        checkout_repo = MagicMock()
        checkout_repo.find_active_by_asset.return_value = checkout

        handler = CancelCheckoutCommandHandler(
            asset_repo=asset_repo, checkout_repo=checkout_repo,
        )
        handler.handle(_make_command(asset_id=asset.id))

        event = asset_repo.save_event.call_args[0][0]
        assert event.data["auto_assigned_reverted"] is True


class TestCancelValidation:
    def test_asset_not_found_raises(self):
        asset_repo = MagicMock()
        asset_repo.find_by_id.return_value = None

        handler = CancelCheckoutCommandHandler(
            asset_repo=asset_repo, checkout_repo=MagicMock(),
        )
        with pytest.raises(AssetNotFoundError):
            handler.handle(_make_command())

    def test_no_active_checkout_raises(self):
        asset = _make_asset()
        asset_repo = MagicMock()
        asset_repo.find_by_id.return_value = asset
        checkout_repo = MagicMock()
        checkout_repo.find_active_by_asset.return_value = None

        handler = CancelCheckoutCommandHandler(
            asset_repo=asset_repo, checkout_repo=checkout_repo,
        )
        with pytest.raises(NoActiveCheckoutError):
            handler.handle(_make_command(asset_id=asset.id))
