import logging
from dataclasses import dataclass

from src.framework.application.command_bus import (
    Command,
    CommandHandler,
)
from core.storage import StorageServiceInterface
from src.procurement_bc.vendor.domain.entities import VendorContractDocument
from src.procurement_bc.vendor.domain.exceptions import ContractNotFoundError
from src.procurement_bc.vendor.domain.repository import (
    VendorContractRepositoryInterface,
    VendorContractDocumentRepositoryInterface,
)

logger = logging.getLogger(__name__)

VENDOR_CONTRACTS_BUCKET = "vendor-contracts"


@dataclass
class UploadContractDocumentCommand(Command):
    contract_id: str
    vendor_id: str
    company_id: str
    filename: str
    content_type: str
    size_bytes: int
    file_data: bytes
    uploaded_by: str
    id: str = ""


class UploadContractDocumentCommandHandler(
    CommandHandler[UploadContractDocumentCommand],
):
    def __init__(
        self,
        contract_repo: VendorContractRepositoryInterface,
        document_repo: VendorContractDocumentRepositoryInterface,
        storage_service: StorageServiceInterface,
    ):
        self.contract_repo = contract_repo
        self.document_repo = document_repo
        self.storage_service = storage_service

    def handle(self, command: UploadContractDocumentCommand) -> None:
        contract = self.contract_repo.find_by_id(
            command.contract_id,
            command.vendor_id,
            command.company_id,
        )
        if not contract:
            raise ContractNotFoundError("Contract not found")

        document = VendorContractDocument.create(
            id=command.id or None,
            contract_id=command.contract_id,
            company_id=command.company_id,
            filename=command.filename,
            content_type=command.content_type,
            size_bytes=command.size_bytes,
            storage_key="",
            uploaded_by=command.uploaded_by,
        )

        storage_key = (
            f"{command.company_id}/{command.vendor_id}"
            f"/{command.contract_id}/{document.id}/{command.filename}"
        )
        self.storage_service.ensure_bucket(VENDOR_CONTRACTS_BUCKET)
        self.storage_service.upload(
            storage_key, command.file_data, command.content_type,
        )
        document.storage_key = storage_key

        self.document_repo.save(document)
        logger.info(
            "Document %s uploaded for contract %s",
            document.id, command.contract_id,
        )
