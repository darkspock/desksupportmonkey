from unittest.mock import MagicMock

from src.procurement_bc.vendor.application.queries.list_vendors import (
    ListVendorsQuery,
    ListVendorsQueryHandler,
)
from src.procurement_bc.vendor.domain.entities import Vendor


class TestListVendorsQueryHandler:
    def test_returns_vendors_and_total(self):
        repo = MagicMock()
        vendor = Vendor.create(
            company_id="comp1", name="Acme",
        )
        repo.find_all.return_value = ([vendor], 1)

        handler = ListVendorsQueryHandler(
            vendor_repo=repo,
        )
        vendors, total = handler.handle(
            ListVendorsQuery(
                company_id="comp1",
                page=1,
                page_size=20,
            )
        )
        assert len(vendors) == 1
        assert total == 1

    def test_passes_filters(self):
        repo = MagicMock()
        repo.find_all.return_value = ([], 0)

        handler = ListVendorsQueryHandler(
            vendor_repo=repo,
        )
        handler.handle(
            ListVendorsQuery(
                company_id="comp1",
                page=2,
                page_size=10,
                search="acme",
                is_active=True,
            )
        )
        repo.find_all.assert_called_once_with(
            company_id="comp1",
            page=2,
            page_size=10,
            search="acme",
            is_active=True,
        )
