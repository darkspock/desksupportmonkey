import logging
from dataclasses import dataclass
from typing import Optional

from src.framework.application.command_bus import Command, CommandHandler
from src.procurement_bc.vendor.domain.entities import VendorDependency
from src.procurement_bc.vendor.domain.enums import BusinessFunction
from src.procurement_bc.vendor.domain.exceptions import VendorNotFoundError
from src.procurement_bc.vendor.domain.repository import (
    VendorDependencyRepositoryInterface,
    VendorRepositoryInterface,
)

logger = logging.getLogger(__name__)


@dataclass
class CreateDependencyCommand(Command):
    vendor_id: str
    company_id: str
    service_description: str
    business_function: str
    is_critical: bool = False
    notes: Optional[str] = None
    id: str = ""
    performed_by: str = ""


class CreateDependencyCommandHandler(
    CommandHandler[CreateDependencyCommand],
):
    def __init__(
        self,
        vendor_repo: VendorRepositoryInterface,
        dependency_repo: VendorDependencyRepositoryInterface,
    ):
        self.vendor_repo = vendor_repo
        self.dependency_repo = dependency_repo

    def handle(self, command: CreateDependencyCommand) -> None:
        vendor = self.vendor_repo.find_by_id(
            command.vendor_id, command.company_id,
        )
        if not vendor:
            raise VendorNotFoundError("Vendor not found")

        dependency = VendorDependency.create(
            id=command.id or None,
            vendor_id=command.vendor_id,
            company_id=command.company_id,
            service_description=command.service_description,
            business_function=BusinessFunction(command.business_function),
            is_critical=command.is_critical,
            notes=command.notes,
        )
        self.dependency_repo.save(dependency)
        logger.info(
            "Dependency %s created for vendor %s",
            dependency.id, command.vendor_id,
        )
