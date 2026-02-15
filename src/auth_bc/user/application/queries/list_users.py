from dataclasses import dataclass
from typing import Optional

from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.repository import UserRepositoryInterface


@dataclass
class ListUsersQuery:
    company_id: str
    page: int = 1
    page_size: int = 20
    role: Optional[str] = None
    is_active: Optional[bool] = None
    department_id: Optional[str] = None
    search: Optional[str] = None


class ListUsersQueryHandler:
    def __init__(self, user_repo: UserRepositoryInterface):
        self.user_repo = user_repo

    def handle(self, query: ListUsersQuery) -> tuple[list[User], int]:
        return self.user_repo.find_all_by_company(
            company_id=query.company_id,
            page=query.page,
            page_size=query.page_size,
            role=query.role,
            is_active=query.is_active,
            department_id=query.department_id,
            search=query.search,
        )
