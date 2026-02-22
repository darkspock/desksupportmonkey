import logging
from dataclasses import dataclass

from src.company_bc.employee_role.domain.repository import EmployeeRoleRepositoryInterface
from src.framework.application.command_bus import Command, CommandHandler

logger = logging.getLogger(__name__)


class EmployeeRoleNotFoundError(Exception):
    pass


class EmployeeRoleInUseError(Exception):
    pass


@dataclass
class DeleteEmployeeRoleCommand(Command):
    role_id: str
    company_id: str


class DeleteEmployeeRoleCommandHandler(CommandHandler[DeleteEmployeeRoleCommand]):
    def __init__(self, role_repo: EmployeeRoleRepositoryInterface):
        self.role_repo = role_repo

    def handle(self, command: DeleteEmployeeRoleCommand) -> None:
        role = self.role_repo.find_by_id(command.role_id, command.company_id)
        if not role:
            raise EmployeeRoleNotFoundError("Employee role not found")

        user_count = self.role_repo.count_users(command.role_id)
        if user_count > 0:
            raise EmployeeRoleInUseError(
                f"Cannot delete role with {user_count} assigned user(s)"
            )

        profile_count = self.role_repo.count_equipment_profiles(command.role_id)
        if profile_count > 0:
            raise EmployeeRoleInUseError(
                f"Cannot delete role with {profile_count} equipment profile(s)"
            )

        self.role_repo.delete(command.role_id)
        logger.info("Employee role deleted: %s", command.role_id)
