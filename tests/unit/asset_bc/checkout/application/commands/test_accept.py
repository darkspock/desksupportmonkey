from unittest.mock import MagicMock

import pytest

from src.asset_bc.checkout.application.commands.accept_checkout import (
    AcceptCheckoutCommand,
    AcceptCheckoutCommandHandler,
)
from src.asset_bc.checkout.domain.entities import AssetCheckout
from src.asset_bc.checkout.domain.enums import AssetCondition
from src.asset_bc.checkout.domain.exceptions import (
    CheckoutAlreadyAcceptedError,
    CheckoutNotOpenError,
    NoActiveCheckoutError,
    UnauthorizedAcceptError,
)


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
        user_id="user1",
    )
    defaults.update(overrides)
    return AcceptCheckoutCommand(**defaults)


class TestAcceptCheckoutHappyPath:
    def test_accept_sets_accepted_at(self):
        checkout = _make_checkout()
        assert checkout.is_accepted is False

        asset_repo = MagicMock()
        checkout_repo = MagicMock()
        checkout_repo.find_active_by_asset.return_value = checkout

        handler = AcceptCheckoutCommandHandler(
            asset_repo=asset_repo, checkout_repo=checkout_repo,
        )
        handler.handle(_make_command())

        assert checkout.is_accepted is True
        assert checkout.accepted_at is not None
        checkout_repo.save.assert_called_once()

    def test_accept_creates_event(self):
        checkout = _make_checkout()

        asset_repo = MagicMock()
        checkout_repo = MagicMock()
        checkout_repo.find_active_by_asset.return_value = checkout

        handler = AcceptCheckoutCommandHandler(
            asset_repo=asset_repo, checkout_repo=checkout_repo,
        )
        handler.handle(_make_command())

        asset_repo.save_event.assert_called_once()
        event = asset_repo.save_event.call_args[0][0]
        assert event.event_type == "checkout_accepted"
        assert event.data["user_id"] == "user1"


class TestAcceptCheckoutValidation:
    def test_no_active_checkout_raises(self):
        checkout_repo = MagicMock()
        checkout_repo.find_active_by_asset.return_value = None

        handler = AcceptCheckoutCommandHandler(
            asset_repo=MagicMock(), checkout_repo=checkout_repo,
        )
        with pytest.raises(NoActiveCheckoutError):
            handler.handle(_make_command())

    def test_wrong_user_raises(self):
        checkout = _make_checkout(user_id="user1")

        checkout_repo = MagicMock()
        checkout_repo.find_active_by_asset.return_value = checkout

        handler = AcceptCheckoutCommandHandler(
            asset_repo=MagicMock(), checkout_repo=checkout_repo,
        )
        with pytest.raises(UnauthorizedAcceptError):
            handler.handle(_make_command(user_id="wrong-user"))

    def test_already_accepted_raises(self):
        checkout = _make_checkout()
        checkout.accept("user1")

        checkout_repo = MagicMock()
        checkout_repo.find_active_by_asset.return_value = checkout

        handler = AcceptCheckoutCommandHandler(
            asset_repo=MagicMock(), checkout_repo=checkout_repo,
        )
        with pytest.raises(CheckoutAlreadyAcceptedError):
            handler.handle(_make_command())

    def test_cancelled_checkout_raises(self):
        checkout = _make_checkout()
        checkout.cancel(cancelled_by="tech1")

        checkout_repo = MagicMock()
        checkout_repo.find_active_by_asset.return_value = checkout

        handler = AcceptCheckoutCommandHandler(
            asset_repo=MagicMock(), checkout_repo=checkout_repo,
        )
        with pytest.raises(CheckoutNotOpenError):
            handler.handle(_make_command())
