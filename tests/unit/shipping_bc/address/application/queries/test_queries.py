from unittest.mock import MagicMock

import pytest

from src.shipping_bc.address.application.queries.addresses_by_user import (
    AddressesByUserQuery,
    AddressesByUserQueryHandler,
)
from src.shipping_bc.address.application.queries.get_address import (
    AddressNotFoundError,
    GetAddressQuery,
    GetAddressQueryHandler,
)
from src.shipping_bc.address.application.queries.list_addresses import (
    ListAddressesQuery,
    ListAddressesQueryHandler,
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


class TestListAddresses:
    def test_list_returns_paginated(self):
        repo = MagicMock()
        repo.find_all.return_value = (
            [_make_address()],
            1,
        )
        handler = ListAddressesQueryHandler(
            address_repo=repo,
        )

        result = handler.handle(
            ListAddressesQuery(
                company_id="comp-1",
            )
        )

        items, total = result
        assert len(items) == 1
        assert total == 1

    def test_list_defaults_active_only(self):
        repo = MagicMock()
        repo.find_all.return_value = ([], 0)
        handler = ListAddressesQueryHandler(
            address_repo=repo,
        )

        handler.handle(
            ListAddressesQuery(
                company_id="comp-1",
            )
        )

        call_kwargs = repo.find_all.call_args[1]
        assert call_kwargs["is_active"] is True


class TestGetAddress:
    def test_get_returns_address(self):
        repo = MagicMock()
        address = _make_address(id="addr-1")
        repo.find_by_id.return_value = address
        handler = GetAddressQueryHandler(
            address_repo=repo,
        )

        result = handler.handle(
            GetAddressQuery(
                address_id="addr-1",
                company_id="comp-1",
            )
        )

        assert result.id == "addr-1"

    def test_get_not_found_raises(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None
        handler = GetAddressQueryHandler(
            address_repo=repo,
        )

        with pytest.raises(AddressNotFoundError):
            handler.handle(
                GetAddressQuery(
                    address_id="nope",
                    company_id="comp-1",
                )
            )


class TestAddressesByUser:
    def test_by_user_returns_addresses(self):
        repo = MagicMock()
        repo.find_by_user_id.return_value = [
            _make_address(),
        ]
        handler = AddressesByUserQueryHandler(
            address_repo=repo,
        )

        result = handler.handle(
            AddressesByUserQuery(
                user_id="user-1",
                company_id="comp-1",
            )
        )

        assert len(result) == 1
        repo.find_by_user_id.assert_called_once_with(
            "user-1", "comp-1",
        )
