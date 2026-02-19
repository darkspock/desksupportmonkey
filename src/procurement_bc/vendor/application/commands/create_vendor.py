import logging
from dataclasses import dataclass
from typing import Optional

from src.framework.application.command_bus import (
    Command,
    CommandHandler,
)
from src.procurement_bc.vendor.domain.entities import (
    Vendor,
)
from src.procurement_bc.vendor.domain.repository import (
    VendorRepositoryInterface,
)

logger = logging.getLogger(__name__)


class DuplicateVendorNameError(Exception):
    pass


@dataclass
class CreateVendorCommand(Command):
    company_id: str
    name: str
    contact_email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    id: str = ""
    performed_by: str = ""


class CreateVendorCommandHandler(
    CommandHandler[CreateVendorCommand],
):
    def __init__(
        self,
        vendor_repo: VendorRepositoryInterface,
    ):
        self.vendor_repo = vendor_repo

    def handle(
        self, command: CreateVendorCommand,
    ) -> None:
        existing = self.vendor_repo.find_by_name(
            command.name.strip(), command.company_id,
        )
        if existing:
            raise DuplicateVendorNameError(
                f"Vendor '{command.name}' already exists",
            )

        vendor = Vendor.create(
            id=command.id or None,
            company_id=command.company_id,
            name=command.name,
            contact_email=command.contact_email,
            phone=command.phone,
            address=command.address,
            notes=command.notes,
        )
        self.vendor_repo.save(vendor)
        logger.info(
            "Vendor %s created for company %s",
            vendor.id,
            command.company_id,
        )
