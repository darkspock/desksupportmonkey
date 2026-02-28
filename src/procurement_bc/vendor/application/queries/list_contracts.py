from dataclasses import dataclass
from typing import Optional

from src.framework.application.query_bus import (
    Query,
    QueryHandler,
)
from src.procurement_bc.vendor.domain.entities import VendorContract
from src.procurement_bc.vendor.domain.enums import ContractStatus
from src.procurement_bc.vendor.domain.repository import (
    VendorContractRepositoryInterface,
)


@dataclass
class ListContractsQuery(Query):
    vendor_id: str
    company_id: str
    page: int = 1
    page_size: int = 20
    status: Optional[str] = None


class ListContractsQueryHandler(
    QueryHandler[
        ListContractsQuery,
        tuple[list[VendorContract], int],
    ],
):
    def __init__(
        self,
        contract_repo: VendorContractRepositoryInterface,
    ):
        self.contract_repo = contract_repo

    def handle(
        self, query: ListContractsQuery,
    ) -> tuple[list[VendorContract], int]:
        status = ContractStatus(query.status) if query.status else None
        return self.contract_repo.find_all_by_vendor(
            vendor_id=query.vendor_id,
            company_id=query.company_id,
            page=query.page,
            page_size=query.page_size,
            status=status,
        )
