import logging
from dataclasses import dataclass
from typing import Optional

from src.auth_bc.user.application.ports import DepartmentLookup
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.repository import UserRepositoryInterface
from src.framework.application.command_bus import Command, CommandHandler

logger = logging.getLogger(__name__)


class UserNotFoundError(Exception):
    pass


class DepartmentNotFoundError(Exception):
    pass


class DepartmentInactiveError(Exception):
    pass


@dataclass
class AssignDepartmentCommand(Command):
    user_id: str
    company_id: str
    department_id: Optional[str]


class AssignDepartmentCommandHandler(CommandHandler[AssignDepartmentCommand]):
    def __init__(
        self,
        user_repo: UserRepositoryInterface,
        department_repo: DepartmentLookup,
    ):
        self.user_repo = user_repo
        self.department_repo = department_repo

    def handle(self, command: AssignDepartmentCommand) -> None:
        user = self.user_repo.find_by_id_and_company(command.user_id, command.company_id)
        if not user:
            raise UserNotFoundError("User not found")

        if command.department_id is not None:
            department = self.department_repo.find_by_id(
                command.department_id, command.company_id
            )
            if not department:
                raise DepartmentNotFoundError("Department not found")
            if not department.is_active:
                raise DepartmentInactiveError("Cannot assign user to inactive department")

        user.assign_department(command.department_id)
        self.user_repo.save(user)
        logger.info("User %s assigned to department %s", user.id, command.department_id)
