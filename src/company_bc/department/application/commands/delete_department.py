import logging
from dataclasses import dataclass

from src.company_bc.department.domain.entities import Department
from src.company_bc.department.domain.repository import DepartmentRepositoryInterface

logger = logging.getLogger(__name__)


class DepartmentNotFoundError(Exception):
    pass


class DepartmentHasUsersError(Exception):
    pass


@dataclass
class DeleteDepartmentCommand:
    department_id: str
    company_id: str


class DeleteDepartmentCommandHandler:
    def __init__(self, department_repo: DepartmentRepositoryInterface):
        self.department_repo = department_repo

    def handle(self, command: DeleteDepartmentCommand) -> Department:
        department = self.department_repo.find_by_id(command.department_id, command.company_id)
        if not department:
            raise DepartmentNotFoundError("Department not found")

        user_count = self.department_repo.count_users(command.department_id)
        if user_count > 0:
            raise DepartmentHasUsersError(
                f"Cannot delete department with {user_count} assigned user(s)"
            )

        department.deactivate()
        self.department_repo.save(department)
        logger.info("Department deactivated: %s", department.id)
        return department
