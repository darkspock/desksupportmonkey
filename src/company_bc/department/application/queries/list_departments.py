from dataclasses import dataclass

from src.company_bc.department.domain.entities import Department
from src.company_bc.department.domain.repository import DepartmentRepositoryInterface
from src.framework.application.query_bus import Query, QueryHandler


@dataclass
class ListDepartmentsQuery(Query):
    company_id: str
    page: int = 1
    page_size: int = 20
    include_inactive: bool = False


class ListDepartmentsQueryHandler(QueryHandler[ListDepartmentsQuery, tuple[list[Department], int]]):
    def __init__(self, department_repo: DepartmentRepositoryInterface):
        self.department_repo = department_repo

    def handle(self, query: ListDepartmentsQuery) -> tuple[list[Department], int]:
        return self.department_repo.find_all(
            company_id=query.company_id,
            page=query.page,
            page_size=query.page_size,
            include_inactive=query.include_inactive,
        )
