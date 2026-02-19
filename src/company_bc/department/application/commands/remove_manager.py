import logging
from dataclasses import dataclass

from src.company_bc.department.domain.repository import (
    DepartmentRepositoryInterface,
)
from src.framework.application.command_bus import Command, CommandHandler

logger = logging.getLogger(__name__)


class DepartmentNotFoundError(Exception):
    pass


@dataclass
class RemoveDepartmentManagerCommand(Command):
    department_id: str
    company_id: str
    performed_by: str


class RemoveDepartmentManagerCommandHandler(
    CommandHandler[RemoveDepartmentManagerCommand],
):
    def __init__(
        self,
        department_repo: DepartmentRepositoryInterface,
    ):
        self.department_repo = department_repo

    def handle(
        self, command: RemoveDepartmentManagerCommand,
    ) -> None:
        department = self.department_repo.find_by_id(
            command.department_id, command.company_id,
        )
        if not department:
            raise DepartmentNotFoundError(
                "Department not found",
            )

        department.remove_manager()
        self.department_repo.save(department)
        logger.info(
            "Manager removed from department %s",
            command.department_id,
        )
