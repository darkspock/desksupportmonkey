from dataclasses import dataclass

from src.company_bc.employee_role.domain.repository import EmployeeRoleRepositoryInterface
from src.company_bc.employee_role.application.queries.get_employee_role import (
    EmployeeRoleReadModel,
)
from src.framework.application.query_bus import Query, QueryHandler


@dataclass
class ListEmployeeRolesQuery(Query):
    company_id: str
    page: int = 1
    page_size: int = 20
    include_inactive: bool = False


class ListEmployeeRolesQueryHandler(
    QueryHandler[ListEmployeeRolesQuery, tuple[list[EmployeeRoleReadModel], int]],
):
    def __init__(self, role_repo: EmployeeRoleRepositoryInterface):
        self.role_repo = role_repo

    def handle(
        self, query: ListEmployeeRolesQuery,
    ) -> tuple[list[EmployeeRoleReadModel], int]:
        roles, total = self.role_repo.find_all(
            company_id=query.company_id,
            page=query.page,
            page_size=query.page_size,
            include_inactive=query.include_inactive,
        )
        return [EmployeeRoleReadModel.from_entity(r) for r in roles], total
