import pytest
from unittest.mock import MagicMock

from src.procurement_bc.vendor.application.commands.create_vendor import (
    CreateVendorCommand,
    CreateVendorCommandHandler,
    DuplicateVendorNameError,
)
from src.procurement_bc.vendor.domain.entities import Vendor


class TestCreateVendorCommandHandler:
    def setup_method(self):
        self.repo = MagicMock()
        self.handler = CreateVendorCommandHandler(
            vendor_repo=self.repo,
        )

    def test_creates_vendor(self):
        self.repo.find_by_name.return_value = None
        self.handler.handle(
            CreateVendorCommand(
                company_id="comp1",
                name="Acme Corp",
                contact_email="sales@acme.com",
                performed_by="user1",
            )
        )
        self.repo.save.assert_called_once()
        saved = self.repo.save.call_args[0][0]
        assert isinstance(saved, Vendor)
        assert saved.name == "Acme Corp"
        assert saved.contact_email == "sales@acme.com"

    def test_duplicate_name_raises(self):
        self.repo.find_by_name.return_value = MagicMock()
        with pytest.raises(DuplicateVendorNameError):
            self.handler.handle(
                CreateVendorCommand(
                    company_id="comp1",
                    name="Acme Corp",
                    performed_by="user1",
                )
            )
        self.repo.save.assert_not_called()

    def test_empty_name_raises(self):
        self.repo.find_by_name.return_value = None
        with pytest.raises(ValueError):
            self.handler.handle(
                CreateVendorCommand(
                    company_id="comp1",
                    name="",
                    performed_by="user1",
                )
            )
