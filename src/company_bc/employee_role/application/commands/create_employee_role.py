import logging
from dataclasses import dataclass
from typing import Optional

from src.company_bc.employee_role.domain.entities import EmployeeRole
from src.company_bc.employee_role.domain.repository import EmployeeRoleRepositoryInterface
from src.framework.application.command_bus import Command, CommandHandler

logger = logging.getLogger(__name__)


class EmployeeRoleNameExistsError(Exception):
    pass


@dataclass
class CreateEmployeeRoleCommand(Command):
    company_id: str
    name: str
    description: Optional[str] = None
    id: Optional[str] = None


class CreateEmployeeRoleCommandHandler(CommandHandler[CreateEmployeeRoleCommand]):
    def __init__(self, role_repo: EmployeeRoleRepositoryInterface):
        self.role_repo = role_repo

    def handle(self, command: CreateEmployeeRoleCommand) -> None:
        existing = self.role_repo.find_by_name(command.name, command.company_id)
        if existing:
            raise EmployeeRoleNameExistsError(f"Employee role '{command.name}' already exists")

        role = EmployeeRole.create(
            company_id=command.company_id,
            name=command.name,
            description=command.description,
            id=command.id,
        )
        self.role_repo.save(role)
        logger.info("Employee role created: %s in company %s", role.name, command.company_id)
