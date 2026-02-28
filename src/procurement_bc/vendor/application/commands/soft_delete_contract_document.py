import logging
from dataclasses import dataclass

from src.framework.application.command_bus import (
    Command,
    CommandHandler,
)
from src.procurement_bc.vendor.domain.exceptions import (
    ContractDocumentNotFoundError,
)
from src.procurement_bc.vendor.domain.repository import (
    VendorContractDocumentRepositoryInterface,
)

logger = logging.getLogger(__name__)


@dataclass
class SoftDeleteContractDocumentCommand(Command):
    document_id: str
    contract_id: str
    company_id: str
    performed_by: str = ""


class SoftDeleteContractDocumentCommandHandler(
    CommandHandler[SoftDeleteContractDocumentCommand],
):
    def __init__(
        self,
        document_repo: VendorContractDocumentRepositoryInterface,
    ):
        self.document_repo = document_repo

    def handle(
        self, command: SoftDeleteContractDocumentCommand,
    ) -> None:
        document = self.document_repo.find_by_id(
            command.document_id,
            command.contract_id,
            command.company_id,
        )
        if not document:
            raise ContractDocumentNotFoundError(
                "Document not found",
            )

        self.document_repo.soft_delete(
            command.document_id,
            command.contract_id,
            command.company_id,
        )
        logger.info(
            "Document %s soft deleted", command.document_id,
        )
