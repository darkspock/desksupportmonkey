import logging
from dataclasses import dataclass

from src.framework.application.command_bus import Command, CommandHandler
from src.procurement_bc.vendor.domain.exceptions import DependencyNotFoundError
from src.procurement_bc.vendor.domain.repository import (
    VendorDependencyRepositoryInterface,
)

logger = logging.getLogger(__name__)


@dataclass
class SoftDeleteDependencyCommand(Command):
    dependency_id: str
    vendor_id: str
    company_id: str
    performed_by: str = ""


class SoftDeleteDependencyCommandHandler(
    CommandHandler[SoftDeleteDependencyCommand],
):
    def __init__(
        self,
        dependency_repo: VendorDependencyRepositoryInterface,
    ):
        self.dependency_repo = dependency_repo

    def handle(self, command: SoftDeleteDependencyCommand) -> None:
        dependency = self.dependency_repo.find_by_id(
            command.dependency_id,
            command.vendor_id,
            command.company_id,
        )
        if not dependency:
            raise DependencyNotFoundError("Dependency not found")

        self.dependency_repo.soft_delete(
            command.dependency_id,
            command.vendor_id,
            command.company_id,
        )
        logger.info(
            "Dependency %s soft-deleted", command.dependency_id,
        )
