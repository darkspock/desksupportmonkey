import logging
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional

from src.framework.application.command_bus import (
    Command,
    CommandHandler,
)
from src.procurement_bc.vendor.domain.enums import ContractType
from src.procurement_bc.vendor.domain.exceptions import ContractNotFoundError
from src.procurement_bc.vendor.domain.repository import (
    VendorContractRepositoryInterface,
)

logger = logging.getLogger(__name__)


@dataclass
class UpdateContractCommand(Command):
    contract_id: str
    vendor_id: str
    company_id: str
    title: Optional[str] = None
    contract_type: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    renewal_date: Optional[date] = None
    auto_renewal: Optional[bool] = None
    annual_value: Optional[Decimal] = None
    currency: Optional[str] = None
    security_clauses: Optional[dict] = None
    notes: Optional[str] = None
    performed_by: str = ""


class UpdateContractCommandHandler(
    CommandHandler[UpdateContractCommand],
):
    def __init__(
        self,
        contract_repo: VendorContractRepositoryInterface,
    ):
        self.contract_repo = contract_repo

    def handle(self, command: UpdateContractCommand) -> None:
        contract = self.contract_repo.find_by_id(
            command.contract_id,
            command.vendor_id,
            command.company_id,
        )
        if not contract:
            raise ContractNotFoundError("Contract not found")

        contract.update(
            title=command.title,
            contract_type=ContractType(command.contract_type) if command.contract_type else None,
            start_date=command.start_date,
            end_date=command.end_date,
            renewal_date=command.renewal_date,
            auto_renewal=command.auto_renewal,
            annual_value=command.annual_value,
            currency=command.currency,
            security_clauses=command.security_clauses,
            notes=command.notes,
        )
        self.contract_repo.save(contract)
        logger.info("Contract %s updated", command.contract_id)
