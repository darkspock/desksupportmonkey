import logging
from dataclasses import dataclass

from core.password import PasswordService
from src.auth_bc.user.domain.enums import UserRole
from src.auth_bc.user.domain.repository import UserRepositoryInterface
from src.framework.application.command_bus import Command, CommandHandler

logger = logging.getLogger(__name__)


class UserNotFoundError(Exception):
    pass


class NotAdminError(Exception):
    pass


class WeakPasswordError(Exception):
    pass


@dataclass
class SetPasswordCommand(Command):
    user_id: str
    password: str


class SetPasswordCommandHandler(CommandHandler[SetPasswordCommand]):
    def __init__(
        self,
        user_repo: UserRepositoryInterface,
        password_service: PasswordService,
    ):
        self.user_repo = user_repo
        self.password_service = password_service

    def handle(self, command: SetPasswordCommand) -> None:
        user = self.user_repo.find_by_id(command.user_id)
        if user is None:
            raise UserNotFoundError("User not found")

        if user.role not in (UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.TECHNICIAN):
            raise NotAdminError("Only admin and technician accounts can set a password")

        if len(command.password) < 8:
            raise WeakPasswordError("Password must be at least 8 characters")

        hashed = self.password_service.hash_password(command.password)
        user.set_password_hash(hashed)
        self.user_repo.save(user)
        logger.info("Password set for user %s", user.id)
