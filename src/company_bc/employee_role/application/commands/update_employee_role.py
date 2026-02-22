import logging
from dataclasses import dataclass
from typing import Optional

from src.company_bc.employee_role.domain.repository import EmployeeRoleRepositoryInterface
from src.framework.application.command_bus import Command, CommandHandler

logger = logging.getLogger(__name__)


class EmployeeRoleNotFoundError(Exception):
    pass


class EmployeeRoleNameExistsError(Exception):
    pass


@dataclass
class UpdateEmployeeRoleCommand(Command):
    role_id: str
    company_id: str
    name: str
    description: Optional[str] = None


class UpdateEmployeeRoleCommandHandler(CommandHandler[UpdateEmployeeRoleCommand]):
    def __init__(self, role_repo: EmployeeRoleRepositoryInterface):
        self.role_repo = role_repo

    def handle(self, command: UpdateEmployeeRoleCommand) -> None:
        role = self.role_repo.find_by_id(command.role_id, command.company_id)
        if not role:
            raise EmployeeRoleNotFoundError("Employee role not found")

        if role.name.lower() != command.name.lower().strip():
            existing = self.role_repo.find_by_name(command.name, command.company_id)
            if existing and existing.id != role.id:
                raise EmployeeRoleNameExistsError(
                    f"Employee role '{command.name}' already exists"
                )

        role.update_name(command.name)
        role.update_description(command.description)
        self.role_repo.save(role)
        logger.info("Employee role updated: %s", command.role_id)
