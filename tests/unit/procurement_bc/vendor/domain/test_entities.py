import pytest

from src.procurement_bc.vendor.domain.entities import Vendor


class TestVendorCreate:
    def test_creates_vendor(self):
        vendor = Vendor.create(
            company_id="comp1",
            name="Acme Corp",
            contact_email="sales@acme.com",
        )
        assert vendor.id is not None
        assert len(vendor.id) == 26
        assert vendor.name == "Acme Corp"
        assert vendor.is_active is True
        assert vendor.contact_email == "sales@acme.com"

    def test_strips_name(self):
        vendor = Vendor.create(
            company_id="comp1",
            name="  Acme Corp  ",
        )
        assert vendor.name == "Acme Corp"

    def test_empty_name_raises(self):
        with pytest.raises(ValueError, match="required"):
            Vendor.create(
                company_id="comp1", name="",
            )

    def test_whitespace_name_raises(self):
        with pytest.raises(ValueError, match="required"):
            Vendor.create(
                company_id="comp1", name="   ",
            )


class TestVendorActivateDeactivate:
    def test_deactivate(self):
        vendor = Vendor.create(
            company_id="comp1", name="Acme",
        )
        vendor.deactivate()
        assert vendor.is_active is False

    def test_activate(self):
        vendor = Vendor.create(
            company_id="comp1", name="Acme",
        )
        vendor.deactivate()
        vendor.activate()
        assert vendor.is_active is True
