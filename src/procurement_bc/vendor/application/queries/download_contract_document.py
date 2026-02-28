from dataclasses import dataclass

from src.framework.application.query_bus import (
    Query,
    QueryHandler,
)
from core.storage import StorageServiceInterface
from src.procurement_bc.vendor.domain.exceptions import (
    ContractDocumentNotFoundError,
)
from src.procurement_bc.vendor.domain.repository import (
    VendorContractDocumentRepositoryInterface,
)


@dataclass
class DownloadResult:
    data: bytes
    filename: str
    content_type: str


@dataclass
class DownloadContractDocumentQuery(Query):
    document_id: str
    contract_id: str
    company_id: str


class DownloadContractDocumentQueryHandler(
    QueryHandler[DownloadContractDocumentQuery, DownloadResult],
):
    def __init__(
        self,
        document_repo: VendorContractDocumentRepositoryInterface,
        storage_service: StorageServiceInterface,
    ):
        self.document_repo = document_repo
        self.storage_service = storage_service

    def handle(
        self, query: DownloadContractDocumentQuery,
    ) -> DownloadResult:
        document = self.document_repo.find_by_id(
            query.document_id,
            query.contract_id,
            query.company_id,
        )
        if not document:
            raise ContractDocumentNotFoundError(
                "Document not found",
            )

        data = self.storage_service.download(document.storage_key)
        return DownloadResult(
            data=data,
            filename=document.filename,
            content_type=document.content_type,
        )
