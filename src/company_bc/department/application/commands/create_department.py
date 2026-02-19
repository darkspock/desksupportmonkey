import logging
from dataclasses import dataclass
from typing import Optional

from src.company_bc.department.domain.entities import Department
from src.company_bc.department.domain.repository import DepartmentRepositoryInterface
from src.framework.application.command_bus import Command, CommandHandler

logger = logging.getLogger(__name__)


class DepartmentNameExistsError(Exception):
    pass


@dataclass
class CreateDepartmentCommand(Command):
    company_id: str
    name: str
    id: Optional[str] = None


class CreateDepartmentCommandHandler(CommandHandler[CreateDepartmentCommand]):
    def __init__(self, department_repo: DepartmentRepositoryInterface):
        self.department_repo = department_repo

    def handle(self, command: CreateDepartmentCommand) -> None:
        existing = self.department_repo.find_by_name(command.name, command.company_id)
        if existing:
            raise DepartmentNameExistsError(f"Department '{command.name}' already exists")

        department = Department.create(
            company_id=command.company_id,
            name=command.name,
            id=command.id,
        )
        self.department_repo.save(department)
        logger.info("Department created: %s in company %s", department.name, command.company_id)
