import logging
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional

from src.framework.application.command_bus import (
    Command,
    CommandHandler,
)
from src.procurement_bc.vendor.domain.entities import VendorContract
from src.procurement_bc.vendor.domain.enums import ContractType
from src.procurement_bc.vendor.domain.exceptions import VendorNotFoundError
from src.procurement_bc.vendor.domain.repository import (
    VendorContractRepositoryInterface,
    VendorRepositoryInterface,
)

logger = logging.getLogger(__name__)


@dataclass
class CreateContractCommand(Command):
    vendor_id: str
    company_id: str
    contract_type: str
    title: str
    start_date: date
    end_date: Optional[date] = None
    renewal_date: Optional[date] = None
    auto_renewal: bool = False
    annual_value: Optional[Decimal] = None
    currency: Optional[str] = None
    security_clauses: Optional[dict] = None
    notes: Optional[str] = None
    id: str = ""
    performed_by: str = ""


class CreateContractCommandHandler(
    CommandHandler[CreateContractCommand],
):
    def __init__(
        self,
        vendor_repo: VendorRepositoryInterface,
        contract_repo: VendorContractRepositoryInterface,
    ):
        self.vendor_repo = vendor_repo
        self.contract_repo = contract_repo

    def handle(self, command: CreateContractCommand) -> None:
        vendor = self.vendor_repo.find_by_id(
            command.vendor_id, command.company_id,
        )
        if not vendor:
            raise VendorNotFoundError("Vendor not found")

        contract = VendorContract.create(
            id=command.id or None,
            vendor_id=command.vendor_id,
            company_id=command.company_id,
            contract_type=ContractType(command.contract_type),
            title=command.title,
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
        logger.info(
            "Contract %s created for vendor %s",
            contract.id, command.vendor_id,
        )
