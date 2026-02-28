from dataclasses import dataclass

from src.framework.application.query_bus import (
    Query,
    QueryHandler,
)
from src.procurement_bc.vendor.domain.entities import VendorContract
from src.procurement_bc.vendor.domain.exceptions import ContractNotFoundError
from src.procurement_bc.vendor.domain.repository import (
    VendorContractRepositoryInterface,
    VendorContractDocumentRepositoryInterface,
)


@dataclass
class ContractDetailResult:
    contract: VendorContract
    document_count: int


@dataclass
class GetContractQuery(Query):
    contract_id: str
    vendor_id: str
    company_id: str


class GetContractQueryHandler(
    QueryHandler[GetContractQuery, ContractDetailResult],
):
    def __init__(
        self,
        contract_repo: VendorContractRepositoryInterface,
        document_repo: VendorContractDocumentRepositoryInterface,
    ):
        self.contract_repo = contract_repo
        self.document_repo = document_repo

    def handle(
        self, query: GetContractQuery,
    ) -> ContractDetailResult:
        contract = self.contract_repo.find_by_id(
            query.contract_id,
            query.vendor_id,
            query.company_id,
        )
        if not contract:
            raise ContractNotFoundError("Contract not found")

        doc_count = self.document_repo.count_by_contract(
            query.contract_id, query.company_id,
        )
        return ContractDetailResult(
            contract=contract,
            document_count=doc_count,
        )
