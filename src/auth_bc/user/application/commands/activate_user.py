import logging
from dataclasses import dataclass

from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.repository import UserRepositoryInterface

logger = logging.getLogger(__name__)


class UserNotFoundError(Exception):
    pass


@dataclass
class ActivateUserCommand:
    user_id: str
    company_id: str


class ActivateUserCommandHandler:
    def __init__(self, user_repo: UserRepositoryInterface):
        self.user_repo = user_repo

    def handle(self, command: ActivateUserCommand) -> User:
        user = self.user_repo.find_by_id_and_company(command.user_id, command.company_id)
        if not user:
            raise UserNotFoundError("User not found")

        user.activate()
        self.user_repo.save(user)
        logger.info("User %s activated", user.id)
        return user
