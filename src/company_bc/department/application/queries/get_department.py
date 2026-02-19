from dataclasses import dataclass

from src.company_bc.department.domain.entities import Department
from src.company_bc.department.domain.repository import DepartmentRepositoryInterface
from src.framework.application.query_bus import Query, QueryHandler


class DepartmentNotFoundError(Exception):
    pass


@dataclass
class DepartmentDetail:
    department: Department
    user_count: int


@dataclass
class GetDepartmentQuery(Query):
    department_id: str
    company_id: str


class GetDepartmentQueryHandler(QueryHandler[GetDepartmentQuery, DepartmentDetail]):
    def __init__(self, department_repo: DepartmentRepositoryInterface):
        self.department_repo = department_repo

    def handle(self, query: GetDepartmentQuery) -> DepartmentDetail:
        department = self.department_repo.find_by_id(query.department_id, query.company_id)
        if not department:
            raise DepartmentNotFoundError("Department not found")

        user_count = self.department_repo.count_users(query.department_id)
        return DepartmentDetail(department=department, user_count=user_count)
