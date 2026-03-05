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


class CannotDeactivateSelfError(Exception):
    pass


@dataclass
class DeactivateUserCommand(Command):
    user_id: str
    company_id: str
    current_user_id: str


class DeactivateUserCommandHandler(CommandHandler[DeactivateUserCommand]):
    def __init__(
        self,
        user_repo: UserRepositoryInterface,
        company_user_repo: Optional[CompanyUserRepositoryInterface] = None,
    ):
        self.user_repo = user_repo
        self.company_user_repo = company_user_repo

    def handle(self, command: DeactivateUserCommand) -> None:
        user = self.user_repo.find_by_id_and_company(command.user_id, command.company_id)
        if not user:
            raise UserNotFoundError("User not found")

        if command.user_id == command.current_user_id:
            raise CannotDeactivateSelfError("Cannot deactivate your own account")

        user.deactivate()
        self.user_repo.save(user)

        # Dual-write: deactivate membership
        if self.company_user_repo:
            membership = self.company_user_repo.find_by_user_and_company(
                user.id, command.company_id
            )
            if membership:
                membership.deactivate()
                self.company_user_repo.save(membership)

        logger.info("User %s deactivated", user.id)
