import logging
from dataclasses import dataclass

from src.framework.application.command_bus import (
    Command,
    CommandHandler,
)
from src.procurement_bc.vendor.domain.enums import ContractStatus
from src.procurement_bc.vendor.domain.exceptions import ContractNotFoundError
from src.procurement_bc.vendor.domain.repository import (
    VendorContractRepositoryInterface,
)

logger = logging.getLogger(__name__)


@dataclass
class ChangeContractStatusCommand(Command):
    contract_id: str
    vendor_id: str
    company_id: str
    new_status: str
    performed_by: str = ""


class ChangeContractStatusCommandHandler(
    CommandHandler[ChangeContractStatusCommand],
):
    def __init__(
        self,
        contract_repo: VendorContractRepositoryInterface,
    ):
        self.contract_repo = contract_repo

    def handle(self, command: ChangeContractStatusCommand) -> None:
        contract = self.contract_repo.find_by_id(
            command.contract_id,
            command.vendor_id,
            command.company_id,
        )
        if not contract:
            raise ContractNotFoundError("Contract not found")

        contract.change_status(ContractStatus(command.new_status))
        self.contract_repo.save(contract)
        logger.info(
            "Contract %s status changed to %s",
            command.contract_id, command.new_status,
        )
