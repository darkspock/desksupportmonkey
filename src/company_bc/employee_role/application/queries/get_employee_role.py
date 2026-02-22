from dataclasses import dataclass
from datetime import datetime

from src.company_bc.employee_role.domain.entities import EmployeeRole
from src.company_bc.employee_role.domain.repository import EmployeeRoleRepositoryInterface
from src.framework.application.query_bus import Query, QueryHandler


class EmployeeRoleNotFoundError(Exception):
    pass


@dataclass
class GetEmployeeRoleQuery(Query):
    role_id: str
    company_id: str


@dataclass
class EmployeeRoleReadModel:
    id: str
    company_id: str
    name: str
    description: str | None
    is_active: bool
    created_at: datetime | None
    updated_at: datetime | None

    @classmethod
    def from_entity(cls, role: EmployeeRole) -> "EmployeeRoleReadModel":
        return cls(
            id=role.id,
            company_id=role.company_id,
            name=role.name,
            description=role.description,
            is_active=role.is_active,
            created_at=role.created_at,
            updated_at=role.updated_at,
        )


class GetEmployeeRoleQueryHandler(
    QueryHandler[GetEmployeeRoleQuery, EmployeeRoleReadModel],
):
    def __init__(self, role_repo: EmployeeRoleRepositoryInterface):
        self.role_repo = role_repo

    def handle(self, query: GetEmployeeRoleQuery) -> EmployeeRoleReadModel:
        role = self.role_repo.find_by_id(query.role_id, query.company_id)
        if not role:
            raise EmployeeRoleNotFoundError("Employee role not found")
        return EmployeeRoleReadModel.from_entity(role)
