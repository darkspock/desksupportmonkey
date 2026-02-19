import logging
from dataclasses import dataclass
from typing import Any, Optional

from src.company_bc.department.domain.repository import (
    DepartmentRepositoryInterface,
)
from src.framework.application.command_bus import Command, CommandHandler

logger = logging.getLogger(__name__)


class DepartmentNotFoundError(Exception):
    pass


class UserNotFoundError(Exception):
    pass


class UserInactiveError(Exception):
    pass


class CrossCompanyError(Exception):
    pass


class UserLookupPort:
    """Protocol for looking up users from company_bc."""

    def find_by_id(self, user_id: str) -> Optional[Any]:
        ...  # pragma: no cover


@dataclass
class AssignDepartmentManagerCommand(Command):
    department_id: str
    company_id: str
    manager_user_id: str
    performed_by: str


class AssignDepartmentManagerCommandHandler(
    CommandHandler[AssignDepartmentManagerCommand],
):
    def __init__(
        self,
        department_repo: DepartmentRepositoryInterface,
        user_lookup: Any,
    ):
        self.department_repo = department_repo
        self.user_lookup = user_lookup

    def handle(
        self, command: AssignDepartmentManagerCommand,
    ) -> None:
        department = self.department_repo.find_by_id(
            command.department_id, command.company_id,
        )
        if not department:
            raise DepartmentNotFoundError(
                "Department not found",
            )

        user = self.user_lookup.find_by_id(
            command.manager_user_id,
        )
        if not user:
            raise UserNotFoundError("User not found")
        if not user.is_active:
            raise UserInactiveError("User is inactive")
        if user.company_id != command.company_id:
            raise CrossCompanyError(
                "User does not belong to the same company",
            )

        department.assign_manager(command.manager_user_id)
        self.department_repo.save(department)
        logger.info(
            "Manager %s assigned to department %s",
            command.manager_user_id,
            command.department_id,
        )
