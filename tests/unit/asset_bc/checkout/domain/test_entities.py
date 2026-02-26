import pytest

from src.asset_bc.checkout.domain.entities import AssetCheckout
from src.asset_bc.checkout.domain.enums import AssetCondition
from src.asset_bc.checkout.domain.exceptions import (
    CheckoutAlreadyAcceptedError,
    CheckoutNotOpenError,
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


class TestAssetCheckoutCreate:
    def test_creates_with_ulid(self):
        checkout = _make_checkout()
        assert checkout.id
        assert len(checkout.id) == 26  # ULID length

    def test_sets_checked_out_at(self):
        checkout = _make_checkout()
        assert checkout.checked_out_at is not None

    def test_initial_state_is_open(self):
        checkout = _make_checkout()
        assert checkout.is_open is True
        assert checkout.is_accepted is False
        assert checkout.is_cancelled is False
        assert checkout.status == "open"

    def test_auto_assigned_default_false(self):
        checkout = _make_checkout()
        assert checkout.auto_assigned is False

    def test_auto_assigned_true(self):
        checkout = _make_checkout(auto_assigned=True)
        assert checkout.auto_assigned is True

    def test_strips_notes(self):
        checkout = _make_checkout(
            condition_out_notes="  some notes  ",
            notes_out="  other notes  ",
        )
        assert checkout.condition_out_notes == "some notes"
        assert checkout.notes_out == "other notes"

    def test_none_notes(self):
        checkout = _make_checkout(condition_out_notes=None, notes_out=None)
        assert checkout.condition_out_notes is None
        assert checkout.notes_out is None

    def test_missing_asset_id_raises(self):
        with pytest.raises(ValueError, match="asset_id"):
            _make_checkout(asset_id="")

    def test_missing_user_id_raises(self):
        with pytest.raises(ValueError, match="user_id"):
            _make_checkout(user_id="")

    def test_missing_checked_out_by_raises(self):
        with pytest.raises(ValueError, match="checked_out_by"):
            _make_checkout(checked_out_by="")

    def test_custom_id(self):
        checkout = _make_checkout(id="custom-id")
        assert checkout.id == "custom-id"


class TestAssetCheckoutAccept:
    def test_accept_happy_path(self):
        checkout = _make_checkout()
        checkout.accept("user1")
        assert checkout.is_accepted is True
        assert checkout.accepted_at is not None
        assert checkout.status == "accepted"

    def test_accept_wrong_user_raises(self):
        checkout = _make_checkout()
        with pytest.raises(UnauthorizedAcceptError):
            checkout.accept("other-user")

    def test_accept_already_accepted_raises(self):
        checkout = _make_checkout()
        checkout.accept("user1")
        with pytest.raises(CheckoutAlreadyAcceptedError):
            checkout.accept("user1")

    def test_accept_not_open_checked_in_raises(self):
        checkout = _make_checkout()
        checkout.checkin(
            checked_in_by="tech1",
            condition_in=AssetCondition.GOOD,
        )
        with pytest.raises(CheckoutNotOpenError):
            checkout.accept("user1")

    def test_accept_not_open_cancelled_raises(self):
        checkout = _make_checkout()
        checkout.cancel(cancelled_by="tech1")
        with pytest.raises(CheckoutNotOpenError):
            checkout.accept("user1")


class TestAssetCheckoutCheckin:
    def test_checkin_happy_path(self):
        checkout = _make_checkout()
        checkout.checkin(
            checked_in_by="tech1",
            condition_in=AssetCondition.FAIR,
            condition_in_notes="Minor scratches",
            notes_in="Returned on time",
        )
        assert checkout.checked_in_at is not None
        assert checkout.checked_in_by == "tech1"
        assert checkout.condition_in == AssetCondition.FAIR
        assert checkout.condition_in_notes == "Minor scratches"
        assert checkout.notes_in == "Returned on time"
        assert checkout.is_open is False
        assert checkout.status == "checked_in"

    def test_checkin_strips_notes(self):
        checkout = _make_checkout()
        checkout.checkin(
            checked_in_by="tech1",
            condition_in=AssetCondition.GOOD,
            condition_in_notes="  padded  ",
            notes_in="  padded  ",
        )
        assert checkout.condition_in_notes == "padded"
        assert checkout.notes_in == "padded"

    def test_checkin_not_open_raises(self):
        checkout = _make_checkout()
        checkout.cancel(cancelled_by="tech1")
        with pytest.raises(CheckoutNotOpenError):
            checkout.checkin(
                checked_in_by="tech1",
                condition_in=AssetCondition.GOOD,
            )


class TestAssetCheckoutCancel:
    def test_cancel_happy_path(self):
        checkout = _make_checkout()
        checkout.cancel(cancelled_by="tech1", reason="Wrong asset")
        assert checkout.cancelled_at is not None
        assert checkout.cancelled_by == "tech1"
        assert checkout.cancel_reason == "Wrong asset"
        assert checkout.is_open is False
        assert checkout.is_cancelled is True
        assert checkout.status == "cancelled"

    def test_cancel_no_reason(self):
        checkout = _make_checkout()
        checkout.cancel(cancelled_by="tech1")
        assert checkout.cancel_reason is None

    def test_cancel_strips_reason(self):
        checkout = _make_checkout()
        checkout.cancel(cancelled_by="tech1", reason="  extra spaces  ")
        assert checkout.cancel_reason == "extra spaces"

    def test_cancel_already_checked_in_raises(self):
        checkout = _make_checkout()
        checkout.checkin(
            checked_in_by="tech1",
            condition_in=AssetCondition.GOOD,
        )
        with pytest.raises(CheckoutNotOpenError):
            checkout.cancel(cancelled_by="tech1")

    def test_cancel_already_cancelled_raises(self):
        checkout = _make_checkout()
        checkout.cancel(cancelled_by="tech1")
        with pytest.raises(CheckoutNotOpenError):
            checkout.cancel(cancelled_by="tech1")


class TestAssetCheckoutProperties:
    def test_is_open_true_for_new(self):
        checkout = _make_checkout()
        assert checkout.is_open is True

    def test_is_open_false_after_checkin(self):
        checkout = _make_checkout()
        checkout.checkin(checked_in_by="tech1", condition_in=AssetCondition.GOOD)
        assert checkout.is_open is False

    def test_is_open_false_after_cancel(self):
        checkout = _make_checkout()
        checkout.cancel(cancelled_by="tech1")
        assert checkout.is_open is False

    def test_status_transitions(self):
        checkout = _make_checkout()
        assert checkout.status == "open"

        checkout.accept("user1")
        assert checkout.status == "accepted"

        checkout.checkin(checked_in_by="tech1", condition_in=AssetCondition.GOOD)
        assert checkout.status == "checked_in"

    def test_status_cancelled(self):
        checkout = _make_checkout()
        checkout.cancel(cancelled_by="tech1")
        assert checkout.status == "cancelled"
