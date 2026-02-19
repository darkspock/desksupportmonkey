from src.shipping_bc.address.domain.entities import (
    ShippingAddress,
)


def _make_address(**overrides):
    defaults = dict(
        company_id="comp1",
        label="HQ Office",
        street_line_1="123 Main St",
        city="Austin",
        state="TX",
        postal_code="78701",
    )
    defaults.update(overrides)
    return ShippingAddress.create(**defaults)


class TestShippingAddressCreate:

    def test_create_generates_ulid(self):
        addr = _make_address()
        assert addr.id is not None
        assert len(addr.id) == 26

    def test_create_defaults_country_us(self):
        addr = _make_address()
        assert addr.country == "US"

    def test_create_is_active_by_default(self):
        addr = _make_address()
        assert addr.is_active is True


class TestShippingAddressDeactivate:

    def test_deactivate_sets_is_active_false(self):
        addr = _make_address()
        addr.deactivate()
        assert addr.is_active is False


class TestShippingAddressUpdate:

    def test_update_modifies_fields(self):
        addr = _make_address()
        addr.update(
            label="New Label",
            city="Dallas",
            state="TX",
            postal_code="75201",
            phone="+1-555-1234",
        )
        assert addr.label == "New Label"
        assert addr.city == "Dallas"
        assert addr.postal_code == "75201"
        assert addr.phone == "+1-555-1234"
        # Unchanged fields
        assert addr.street_line_1 == "123 Main St"
        assert addr.country == "US"
