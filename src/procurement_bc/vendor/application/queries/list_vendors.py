from dataclasses import dataclass
from typing import Optional

from src.framework.application.query_bus import (
    Query,
    QueryHandler,
)
from src.procurement_bc.vendor.domain.entities import (
    Vendor,
)
from src.procurement_bc.vendor.domain.repository import (
    VendorRepositoryInterface,
)


@dataclass
class ListVendorsQuery(Query):
    company_id: str
    page: int = 1
    page_size: int = 20
    search: Optional[str] = None
    is_active: Optional[bool] = None


class ListVendorsQueryHandler(
    QueryHandler[
        ListVendorsQuery,
        tuple[list[Vendor], int],
    ],
):
    def __init__(
        self,
        vendor_repo: VendorRepositoryInterface,
    ):
        self.vendor_repo = vendor_repo

    def handle(
        self, query: ListVendorsQuery,
    ) -> tuple[list[Vendor], int]:
        return self.vendor_repo.find_all(
            company_id=query.company_id,
            page=query.page,
            page_size=query.page_size,
            search=query.search,
            is_active=query.is_active,
        )
