import logging
from dataclasses import dataclass

from src.framework.application.command_bus import (
    Command,
    CommandHandler,
)
from src.procurement_bc.vendor.domain.exceptions import ContractNotFoundError
from src.procurement_bc.vendor.domain.repository import (
    VendorContractRepositoryInterface,
)

logger = logging.getLogger(__name__)


@dataclass
class SoftDeleteContractCommand(Command):
    contract_id: str
    vendor_id: str
    company_id: str
    performed_by: str = ""


class SoftDeleteContractCommandHandler(
    CommandHandler[SoftDeleteContractCommand],
):
    def __init__(
        self,
        contract_repo: VendorContractRepositoryInterface,
    ):
        self.contract_repo = contract_repo

    def handle(self, command: SoftDeleteContractCommand) -> None:
        contract = self.contract_repo.find_by_id(
            command.contract_id,
            command.vendor_id,
            command.company_id,
        )
        if not contract:
            raise ContractNotFoundError("Contract not found")

        self.contract_repo.soft_delete(
            command.contract_id,
            command.vendor_id,
            command.company_id,
        )
        logger.info("Contract %s soft deleted", command.contract_id)
