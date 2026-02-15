import logging
from dataclasses import dataclass

from src.company_bc.department.domain.entities import Department
from src.company_bc.department.domain.repository import DepartmentRepositoryInterface

logger = logging.getLogger(__name__)


class DepartmentNameExistsError(Exception):
    pass


@dataclass
class CreateDepartmentCommand:
    company_id: str
    name: str


class CreateDepartmentCommandHandler:
    def __init__(self, department_repo: DepartmentRepositoryInterface):
        self.department_repo = department_repo

    def handle(self, command: CreateDepartmentCommand) -> Department:
        existing = self.department_repo.find_by_name(command.name, command.company_id)
        if existing:
            raise DepartmentNameExistsError(f"Department '{command.name}' already exists")

        department = Department.create(
            company_id=command.company_id,
            name=command.name,
        )
        self.department_repo.save(department)
        logger.info("Department created: %s in company %s", department.name, command.company_id)
        return department
