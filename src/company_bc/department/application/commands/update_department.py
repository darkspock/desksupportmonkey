import logging
from dataclasses import dataclass

from src.company_bc.department.domain.entities import Department
from src.company_bc.department.domain.repository import DepartmentRepositoryInterface

logger = logging.getLogger(__name__)


class DepartmentNotFoundError(Exception):
    pass


class DepartmentNameExistsError(Exception):
    pass


@dataclass
class UpdateDepartmentCommand:
    department_id: str
    company_id: str
    name: str


class UpdateDepartmentCommandHandler:
    def __init__(self, department_repo: DepartmentRepositoryInterface):
        self.department_repo = department_repo

    def handle(self, command: UpdateDepartmentCommand) -> Department:
        department = self.department_repo.find_by_id(command.department_id, command.company_id)
        if not department:
            raise DepartmentNotFoundError("Department not found")

        existing = self.department_repo.find_by_name(command.name, command.company_id)
        if existing and existing.id != department.id:
            raise DepartmentNameExistsError(f"Department '{command.name}' already exists")

        department.update_name(command.name)
        self.department_repo.save(department)
        logger.info("Department updated: %s", department.id)
        return department
