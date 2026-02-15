from dataclasses import dataclass

from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.repository import UserRepositoryInterface


class UserNotFoundError(Exception):
    pass


@dataclass
class GetUserDetailQuery:
    user_id: str
    company_id: str


class GetUserDetailQueryHandler:
    def __init__(self, user_repo: UserRepositoryInterface):
        self.user_repo = user_repo

    def handle(self, query: GetUserDetailQuery) -> User:
        user = self.user_repo.find_by_id_and_company(query.user_id, query.company_id)
        if not user:
            raise UserNotFoundError("User not found")
        return user
