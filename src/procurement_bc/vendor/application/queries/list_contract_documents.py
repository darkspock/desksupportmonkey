from dataclasses import dataclass

from src.framework.application.query_bus import (
    Query,
    QueryHandler,
)
from src.procurement_bc.vendor.domain.entities import VendorContractDocument
from src.procurement_bc.vendor.domain.repository import (
    VendorContractDocumentRepositoryInterface,
)


@dataclass
class ListContractDocumentsQuery(Query):
    contract_id: str
    company_id: str


class ListContractDocumentsQueryHandler(
    QueryHandler[
        ListContractDocumentsQuery,
        list[VendorContractDocument],
    ],
):
    def __init__(
        self,
        document_repo: VendorContractDocumentRepositoryInterface,
    ):
        self.document_repo = document_repo

    def handle(
        self, query: ListContractDocumentsQuery,
    ) -> list[VendorContractDocument]:
        return self.document_repo.find_all_by_contract(
            query.contract_id, query.company_id,
        )
