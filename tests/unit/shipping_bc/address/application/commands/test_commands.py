from unittest.mock import MagicMock

import pytest

from src.shipping_bc.address.application.commands.create_address import (
    CreateAddressCommand,
    CreateAddressCommandHandler,
)
from src.shipping_bc.address.application.commands.deactivate_address import (
    AddressNotFoundError as DeactivateNotFoundError,
    DeactivateAddressCommand,
    DeactivateAddressCommandHandler,
)
from src.shipping_bc.address.application.commands.update_address import (
    AddressNotFoundError as UpdateNotFoundError,
    UpdateAddressCommand,
    UpdateAddressCommandHandler,
)
from src.shipping_bc.address.domain.entities import (
    ShippingAddress,
)


def _make_address(**overrides):
    defaults = dict(
        company_id="comp-1",
        label="Office",
        street_line_1="123 Main St",
        city="Austin",
        state="TX",
        postal_code="78701",
    )
    defaults.update(overrides)
    return ShippingAddress.create(**defaults)


class TestCreateAddress:
    def test_create_address_saves(self):
        repo = MagicMock()
        handler = CreateAddressCommandHandler(
            address_repo=repo,
        )

        handler.handle(
            CreateAddressCommand(
                address_id="addr-1",
                company_id="comp-1",
                label="HQ",
                street_line_1="123 Main St",
                city="Austin",
                state="TX",
                postal_code="78701",
            )
        )

        repo.save.assert_called_once()
        saved = repo.save.call_args[0][0]
        assert saved.id == "addr-1"
        assert saved.label == "HQ"

    def test_create_address_defaults_country(self):
        repo = MagicMock()
        handler = CreateAddressCommandHandler(
            address_repo=repo,
        )

        handler.handle(
            CreateAddressCommand(
                address_id="addr-2",
                company_id="comp-1",
                label="Warehouse",
                street_line_1="456 Industrial Blvd",
                city="Austin",
                state="TX",
                postal_code="78702",
            )
        )

        saved = repo.save.call_args[0][0]
        assert saved.country == "US"


class TestUpdateAddress:
    def test_update_address_modifies_fields(self):
        repo = MagicMock()
        address = _make_address(id="addr-1")
        repo.find_by_id.return_value = address
        handler = UpdateAddressCommandHandler(
            address_repo=repo,
        )

        handler.handle(
            UpdateAddressCommand(
                address_id="addr-1",
                company_id="comp-1",
                label="New Label",
                city="Dallas",
            )
        )

        repo.save.assert_called_once()
        saved = repo.save.call_args[0][0]
        assert saved.label == "New Label"
        assert saved.city == "Dallas"
        assert saved.state == "TX"  # unchanged

    def test_update_not_found_raises(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None
        handler = UpdateAddressCommandHandler(
            address_repo=repo,
        )

        with pytest.raises(UpdateNotFoundError):
            handler.handle(
                UpdateAddressCommand(
                    address_id="nope",
                    company_id="comp-1",
                    label="New",
                )
            )


class TestDeactivateAddress:
    def test_deactivate_sets_inactive(self):
        repo = MagicMock()
        address = _make_address(id="addr-1")
        repo.find_by_id.return_value = address
        handler = DeactivateAddressCommandHandler(
            address_repo=repo,
        )

        handler.handle(
            DeactivateAddressCommand(
                address_id="addr-1",
                company_id="comp-1",
            )
        )

        repo.save.assert_called_once()
        saved = repo.save.call_args[0][0]
        assert saved.is_active is False

    def test_deactivate_not_found_raises(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None
        handler = DeactivateAddressCommandHandler(
            address_repo=repo,
        )

        with pytest.raises(DeactivateNotFoundError):
            handler.handle(
                DeactivateAddressCommand(
                    address_id="nope",
                    company_id="comp-1",
                )
            )
