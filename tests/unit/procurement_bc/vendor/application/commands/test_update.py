import pytest
from unittest.mock import MagicMock

from src.procurement_bc.vendor.application.commands.update_vendor import (
    UpdateVendorCommand,
    UpdateVendorCommandHandler,
    VendorNotFoundError,
)
from src.procurement_bc.vendor.domain.entities import Vendor


class TestUpdateVendorCommandHandler:
    def setup_method(self):
        self.repo = MagicMock()
        self.handler = UpdateVendorCommandHandler(
            vendor_repo=self.repo,
        )

    def test_updates_vendor(self):
        vendor = Vendor.create(
            company_id="comp1", name="Old Name",
        )
        self.repo.find_by_id.return_value = vendor
        self.handler.handle(
            UpdateVendorCommand(
                vendor_id=vendor.id,
                company_id="comp1",
                name="New Name",
                contact_email="new@email.com",
                performed_by="user1",
            )
        )
        self.repo.save.assert_called_once()
        assert vendor.name == "New Name"
        assert vendor.contact_email == "new@email.com"

    def test_not_found_raises(self):
        self.repo.find_by_id.return_value = None
        with pytest.raises(VendorNotFoundError):
            self.handler.handle(
                UpdateVendorCommand(
                    vendor_id="nope",
                    company_id="comp1",
                    name="Name",
                    performed_by="user1",
                )
            )
