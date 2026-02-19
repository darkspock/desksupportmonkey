import logging
from dataclasses import dataclass

from src.framework.application.command_bus import (
    Command,
    CommandHandler,
)
from src.procurement_bc.vendor.domain.repository import (
    VendorRepositoryInterface,
)

logger = logging.getLogger(__name__)


class VendorNotFoundError(Exception):
    pass


@dataclass
class DeactivateVendorCommand(Command):
    vendor_id: str
    company_id: str
    performed_by: str = ""


class DeactivateVendorCommandHandler(
    CommandHandler[DeactivateVendorCommand],
):
    def __init__(
        self,
        vendor_repo: VendorRepositoryInterface,
    ):
        self.vendor_repo = vendor_repo

    def handle(
        self, command: DeactivateVendorCommand,
    ) -> None:
        vendor = self.vendor_repo.find_by_id(
            command.vendor_id, command.company_id,
        )
        if not vendor:
            raise VendorNotFoundError(
                "Vendor not found",
            )

        vendor.deactivate()
        self.vendor_repo.save(vendor)
        logger.info(
            "Vendor %s deactivated", command.vendor_id,
        )
