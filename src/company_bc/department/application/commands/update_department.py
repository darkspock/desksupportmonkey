import logging
from dataclasses import dataclass
from typing import Optional

from src.company_bc.department.domain.entities import Department
from src.company_bc.department.domain.repository import DepartmentRepositoryInterface
from src.framework.application.command_bus import Command, CommandHandler

logger = logging.getLogger(__name__)


class DepartmentNotFoundError(Exception):
    pass


class DepartmentNameExistsError(Exception):
    pass


@dataclass
class UpdateDepartmentCommand(Command):
    department_id: str
    company_id: str
    name: str
    priority_weight: Optional[int] = None
    budget_enforcement_enabled: Optional[bool] = None


class UpdateDepartmentCommandHandler(CommandHandler[UpdateDepartmentCommand]):
    def __init__(self, department_repo: DepartmentRepositoryInterface):
        self.department_repo = department_repo

    def handle(self, command: UpdateDepartmentCommand) -> None:
        department = self.department_repo.find_by_id(command.department_id, command.company_id)
        if not department:
            raise DepartmentNotFoundError("Department not found")

        existing = self.department_repo.find_by_name(command.name, command.company_id)
        if existing and existing.id != department.id:
            raise DepartmentNameExistsError(f"Department '{command.name}' already exists")

        department.update_name(command.name)
        if command.priority_weight is not None:
            department.set_priority_weight(command.priority_weight)
        if command.budget_enforcement_enabled is not None:
            department.set_budget_enforcement_enabled(command.budget_enforcement_enabled)
        self.department_repo.save(department)
        logger.info("Department updated: %s", department.id)
