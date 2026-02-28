import logging
from dataclasses import dataclass
from typing import Optional

from src.framework.application.command_bus import Command, CommandHandler
from src.procurement_bc.vendor.domain.enums import BusinessFunction
from src.procurement_bc.vendor.domain.exceptions import DependencyNotFoundError
from src.procurement_bc.vendor.domain.repository import (
    VendorDependencyRepositoryInterface,
)

logger = logging.getLogger(__name__)


@dataclass
class UpdateDependencyCommand(Command):
    dependency_id: str
    vendor_id: str
    company_id: str
    service_description: Optional[str] = None
    business_function: Optional[str] = None
    is_critical: Optional[bool] = None
    notes: Optional[str] = None
    performed_by: str = ""


class UpdateDependencyCommandHandler(
    CommandHandler[UpdateDependencyCommand],
):
    def __init__(
        self,
        dependency_repo: VendorDependencyRepositoryInterface,
    ):
        self.dependency_repo = dependency_repo

    def handle(self, command: UpdateDependencyCommand) -> None:
        dependency = self.dependency_repo.find_by_id(
            command.dependency_id,
            command.vendor_id,
            command.company_id,
        )
        if not dependency:
            raise DependencyNotFoundError("Dependency not found")

        dependency.update(
            service_description=command.service_description,
            business_function=BusinessFunction(command.business_function) if command.business_function else None,
            is_critical=command.is_critical,
            notes=command.notes,
        )
        self.dependency_repo.save(dependency)
        logger.info(
            "Dependency %s updated", command.dependency_id,
        )
