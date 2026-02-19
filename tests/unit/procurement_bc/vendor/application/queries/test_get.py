import pytest
from unittest.mock import MagicMock

from src.procurement_bc.vendor.application.queries.get_vendor import (
    GetVendorQuery,
    GetVendorQueryHandler,
    VendorNotFoundError,
)
from src.procurement_bc.vendor.domain.entities import Vendor


class TestGetVendorQueryHandler:
    def test_returns_vendor(self):
        repo = MagicMock()
        vendor = Vendor.create(
            company_id="comp1", name="Acme",
        )
        repo.find_by_id.return_value = vendor

        handler = GetVendorQueryHandler(
            vendor_repo=repo,
        )
        result = handler.handle(
            GetVendorQuery(
                vendor_id=vendor.id,
                company_id="comp1",
            )
        )
        assert result.name == "Acme"

    def test_not_found_raises(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None

        handler = GetVendorQueryHandler(
            vendor_repo=repo,
        )
        with pytest.raises(VendorNotFoundError):
            handler.handle(
                GetVendorQuery(
                    vendor_id="nope",
                    company_id="comp1",
                )
            )
