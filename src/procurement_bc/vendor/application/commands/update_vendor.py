import logging
from dataclasses import dataclass
from typing import Optional

from src.framework.application.command_bus import (
    Command,
    CommandHandler,
)
from src.procurement_bc.vendor.domain.enums import VendorCategory
from src.procurement_bc.vendor.domain.exceptions import VendorNotFoundError
from src.procurement_bc.vendor.domain.repository import (
    VendorRepositoryInterface,
)

logger = logging.getLogger(__name__)


@dataclass
class UpdateVendorCommand(Command):
    vendor_id: str
    company_id: str
    name: str
    contact_email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    category: Optional[str] = None
    website: Optional[str] = None
    is_critical_ict: Optional[bool] = None
    performed_by: str = ""


class UpdateVendorCommandHandler(
    CommandHandler[UpdateVendorCommand],
):
    def __init__(
        self,
        vendor_repo: VendorRepositoryInterface,
    ):
        self.vendor_repo = vendor_repo

    def handle(
        self, command: UpdateVendorCommand,
    ) -> None:
        vendor = self.vendor_repo.find_by_id(
            command.vendor_id, command.company_id,
        )
        if not vendor:
            raise VendorNotFoundError(
                "Vendor not found",
            )

        if not command.name or not command.name.strip():
            raise ValueError("Vendor name is required")

        vendor.name = command.name.strip()
        vendor.contact_email = command.contact_email
        vendor.phone = command.phone
        vendor.address = command.address
        vendor.notes = command.notes
        vendor.update_extended_fields(
            category=VendorCategory(command.category) if command.category else None,
            website=command.website,
            is_critical_ict=command.is_critical_ict,
        )
        self.vendor_repo.save(vendor)
        logger.info(
            "Vendor %s updated", command.vendor_id,
        )
