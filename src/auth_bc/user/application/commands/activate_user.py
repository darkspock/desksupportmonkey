import logging
from dataclasses import dataclass
from typing import Optional

from src.auth_bc.company_user.domain.repository import CompanyUserRepositoryInterface
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.repository import UserRepositoryInterface
from src.framework.application.command_bus import Command, CommandHandler

logger = logging.getLogger(__name__)


class UserNotFoundError(Exception):
    pass


@dataclass
class ActivateUserCommand(Command):
    user_id: str
    company_id: str


class ActivateUserCommandHandler(CommandHandler[ActivateUserCommand]):
    def __init__(
        self,
        user_repo: UserRepositoryInterface,
        company_user_repo: Optional[CompanyUserRepositoryInterface] = None,
    ):
        self.user_repo = user_repo
        self.company_user_repo = company_user_repo

    def handle(self, command: ActivateUserCommand) -> None:
        user = self.user_repo.find_by_id_and_company(command.user_id, command.company_id)
        if not user:
            raise UserNotFoundError("User not found")

        user.activate()
        self.user_repo.save(user)

        # Dual-write: activate membership
        if self.company_user_repo:
            membership = self.company_user_repo.find_by_user_and_company(
                user.id, command.company_id
            )
            if membership:
                membership.activate()
                self.company_user_repo.save(membership)

        logger.info("User %s activated", user.id)
