import pytest
from unittest.mock import MagicMock

from src.procurement_bc.vendor.application.commands.activate_vendor import (
    ActivateVendorCommand,
    ActivateVendorCommandHandler,
    VendorNotFoundError as ActivateNotFoundError,
)
from src.procurement_bc.vendor.application.commands.deactivate_vendor import (
    DeactivateVendorCommand,
    DeactivateVendorCommandHandler,
    VendorNotFoundError as DeactivateNotFoundError,
)
from src.procurement_bc.vendor.domain.entities import Vendor


class TestActivateVendorCommandHandler:
    def test_activates_vendor(self):
        repo = MagicMock()
        vendor = Vendor.create(
            company_id="comp1", name="Acme",
        )
        vendor.deactivate()
        repo.find_by_id.return_value = vendor

        handler = ActivateVendorCommandHandler(
            vendor_repo=repo,
        )
        handler.handle(
            ActivateVendorCommand(
                vendor_id=vendor.id,
                company_id="comp1",
                performed_by="user1",
            )
        )
        assert vendor.is_active is True
        repo.save.assert_called_once()

    def test_not_found_raises(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None
        handler = ActivateVendorCommandHandler(
            vendor_repo=repo,
        )
        with pytest.raises(ActivateNotFoundError):
            handler.handle(
                ActivateVendorCommand(
                    vendor_id="nope",
                    company_id="comp1",
                    performed_by="user1",
                )
            )


class TestDeactivateVendorCommandHandler:
    def test_deactivates_vendor(self):
        repo = MagicMock()
        vendor = Vendor.create(
            company_id="comp1", name="Acme",
        )
        repo.find_by_id.return_value = vendor

        handler = DeactivateVendorCommandHandler(
            vendor_repo=repo,
        )
        handler.handle(
            DeactivateVendorCommand(
                vendor_id=vendor.id,
                company_id="comp1",
                performed_by="user1",
            )
        )
        assert vendor.is_active is False
        repo.save.assert_called_once()

    def test_not_found_raises(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None
        handler = DeactivateVendorCommandHandler(
            vendor_repo=repo,
        )
        with pytest.raises(DeactivateNotFoundError):
            handler.handle(
                DeactivateVendorCommand(
                    vendor_id="nope",
                    company_id="comp1",
                    performed_by="user1",
                )
            )
