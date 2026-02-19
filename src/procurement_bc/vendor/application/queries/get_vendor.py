from dataclasses import dataclass

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


class VendorNotFoundError(Exception):
    pass


@dataclass
class GetVendorQuery(Query):
    vendor_id: str
    company_id: str


class GetVendorQueryHandler(
    QueryHandler[GetVendorQuery, Vendor],
):
    def __init__(
        self,
        vendor_repo: VendorRepositoryInterface,
    ):
        self.vendor_repo = vendor_repo

    def handle(
        self, query: GetVendorQuery,
    ) -> Vendor:
        vendor = self.vendor_repo.find_by_id(
            query.vendor_id, query.company_id,
        )
        if not vendor:
            raise VendorNotFoundError(
                "Vendor not found",
            )
        return vendor
