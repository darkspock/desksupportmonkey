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
class ActivateVendorCommand(Command):
    vendor_id: str
    company_id: str
    performed_by: str = ""


class ActivateVendorCommandHandler(
    CommandHandler[ActivateVendorCommand],
):
    def __init__(
        self,
        vendor_repo: VendorRepositoryInterface,
    ):
        self.vendor_repo = vendor_repo

    def handle(
        self, command: ActivateVendorCommand,
    ) -> None:
        vendor = self.vendor_repo.find_by_id(
            command.vendor_id, command.company_id,
        )
        if not vendor:
            raise VendorNotFoundError(
                "Vendor not found",
            )

        vendor.activate()
        self.vendor_repo.save(vendor)
        logger.info(
            "Vendor %s activated", command.vendor_id,
        )
