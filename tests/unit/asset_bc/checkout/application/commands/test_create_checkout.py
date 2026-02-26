from unittest.mock import MagicMock

import pytest

from src.asset_bc.asset.domain.entities import Asset
from src.asset_bc.asset.domain.enums import AssetStatus
from src.asset_bc.checkout.application.commands.create_checkout import (
    AssetNotFoundError,
    CreateCheckoutCommand,
    CreateCheckoutCommandHandler,
    UserInactiveError,
    UserNotFoundError,
)
from src.asset_bc.checkout.domain.exceptions import (
    ActiveCheckoutExistsError,
    AssetAssignedToOtherError,
    InvalidCheckoutAssetStatusError,
)


def _make_asset(**overrides):
    defaults = dict(
        company_id="comp1", type="laptop",
        brand="Dell", model="Latitude", serial_number="SN001",
    )
    defaults.update(overrides)
    return Asset.create(**defaults)


def _make_user_mock(is_active=True, department_id="dept1"):
    user = MagicMock()
    user.id = "user1"
    user.is_active = is_active
    user.department_id = department_id
    return user


def _make_command(**overrides):
    defaults = dict(
        checkout_id="checkout1",
        company_id="comp1",
        asset_id="asset1",
        user_id="user1",
        performed_by="tech1",
        condition_out="good",
    )
    defaults.update(overrides)
    return CreateCheckoutCommand(**defaults)


def _make_handler(asset_repo=None, checkout_repo=None, user_repo=None):
    return CreateCheckoutCommandHandler(
        asset_repo=asset_repo or MagicMock(),
        checkout_repo=checkout_repo or MagicMock(),
        user_repo=user_repo or MagicMock(),
    )


class TestCreateCheckoutFromInStock:
    def test_auto_assigns_and_creates_checkout(self):
        asset = _make_asset()
        assert asset.status == AssetStatus.IN_STOCK

        asset_repo = MagicMock()
        asset_repo.find_by_id.return_value = asset
        checkout_repo = MagicMock()
        checkout_repo.find_active_by_asset.return_value = None
        user_repo = MagicMock()
        user_repo.find_by_id_and_company.return_value = _make_user_mock()

        handler = _make_handler(asset_repo, checkout_repo, user_repo)
        handler.handle(_make_command(asset_id=asset.id))

        # Asset saved (auto-assign)
        asset_repo.save.assert_called_once()
        assert asset.assigned_to == "user1"
        assert asset.status == AssetStatus.ASSIGNED

        # Checkout saved
        checkout_repo.save.assert_called_once()
        saved = checkout_repo.save.call_args[0][0]
        assert saved.auto_assigned is True

        # Two events: assigned + checked_out
        assert asset_repo.save_event.call_count == 2
        events = [c[0][0] for c in asset_repo.save_event.call_args_list]
        assert events[0].event_type == "assigned"
        assert events[1].event_type == "checked_out"


class TestCreateCheckoutFromAssigned:
    def test_same_user_creates_checkout(self):
        asset = _make_asset()
        asset.assign(user_id="user1", department_id="dept1")

        asset_repo = MagicMock()
        asset_repo.find_by_id.return_value = asset
        checkout_repo = MagicMock()
        checkout_repo.find_active_by_asset.return_value = None
        user_repo = MagicMock()
        user_repo.find_by_id_and_company.return_value = _make_user_mock()

        handler = _make_handler(asset_repo, checkout_repo, user_repo)
        handler.handle(_make_command(asset_id=asset.id))

        # No auto-assign save (asset already assigned)
        asset_repo.save.assert_not_called()

        checkout_repo.save.assert_called_once()
        saved = checkout_repo.save.call_args[0][0]
        assert saved.auto_assigned is False

        # Only checked_out event (no assign event)
        assert asset_repo.save_event.call_count == 1
        event = asset_repo.save_event.call_args[0][0]
        assert event.event_type == "checked_out"

    def test_different_user_raises(self):
        asset = _make_asset()
        asset.assign(user_id="other-user", department_id="dept1")

        asset_repo = MagicMock()
        asset_repo.find_by_id.return_value = asset
        user_repo = MagicMock()
        user_repo.find_by_id_and_company.return_value = _make_user_mock()

        handler = _make_handler(asset_repo, user_repo=user_repo)

        with pytest.raises(AssetAssignedToOtherError):
            handler.handle(_make_command(asset_id=asset.id))


class TestCreateCheckoutValidation:
    def test_asset_not_found_raises(self):
        asset_repo = MagicMock()
        asset_repo.find_by_id.return_value = None

        handler = _make_handler(asset_repo)
        with pytest.raises(AssetNotFoundError):
            handler.handle(_make_command())

    def test_user_not_found_raises(self):
        asset = _make_asset()
        asset_repo = MagicMock()
        asset_repo.find_by_id.return_value = asset
        user_repo = MagicMock()
        user_repo.find_by_id_and_company.return_value = None

        handler = _make_handler(asset_repo, user_repo=user_repo)
        with pytest.raises(UserNotFoundError):
            handler.handle(_make_command(asset_id=asset.id))

    def test_user_inactive_raises(self):
        asset = _make_asset()
        asset_repo = MagicMock()
        asset_repo.find_by_id.return_value = asset
        user_repo = MagicMock()
        user_repo.find_by_id_and_company.return_value = _make_user_mock(is_active=False)

        handler = _make_handler(asset_repo, user_repo=user_repo)
        with pytest.raises(UserInactiveError):
            handler.handle(_make_command(asset_id=asset.id))

    def test_invalid_asset_status_raises(self):
        asset = _make_asset()
        asset.change_status(AssetStatus.IN_REPAIR)

        asset_repo = MagicMock()
        asset_repo.find_by_id.return_value = asset
        user_repo = MagicMock()
        user_repo.find_by_id_and_company.return_value = _make_user_mock()

        handler = _make_handler(asset_repo, user_repo=user_repo)
        with pytest.raises(InvalidCheckoutAssetStatusError):
            handler.handle(_make_command(asset_id=asset.id))

    def test_active_checkout_exists_raises(self):
        asset = _make_asset()
        asset.assign(user_id="user1", department_id="dept1")

        asset_repo = MagicMock()
        asset_repo.find_by_id.return_value = asset
        checkout_repo = MagicMock()
        checkout_repo.find_active_by_asset.return_value = MagicMock()  # existing checkout
        user_repo = MagicMock()
        user_repo.find_by_id_and_company.return_value = _make_user_mock()

        handler = _make_handler(asset_repo, checkout_repo, user_repo)
        with pytest.raises(ActiveCheckoutExistsError):
            handler.handle(_make_command(asset_id=asset.id))
