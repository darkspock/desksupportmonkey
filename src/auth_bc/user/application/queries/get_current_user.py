import logging
from dataclasses import dataclass
from typing import Optional

from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.repository import UserRepositoryInterface
from src.framework.application.query_bus import Query, QueryHandler

logger = logging.getLogger(__name__)


@dataclass
class GetCurrentUserQuery(Query):
    user_id: str


class GetCurrentUserQueryHandler(QueryHandler[GetCurrentUserQuery, Optional[User]]):
    def __init__(self, user_repo: UserRepositoryInterface):
        self.user_repo = user_repo

    def handle(self, query: GetCurrentUserQuery) -> Optional[User]:
        user = self.user_repo.find_by_id(query.user_id)
        if user is None:
            return None
        if not user.is_active:
            return None
        return user
