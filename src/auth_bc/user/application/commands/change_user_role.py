import logging
from dataclasses import dataclass

from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
from src.auth_bc.user.domain.repository import UserRepositoryInterface

logger = logging.getLogger(__name__)


class UserNotFoundError(Exception):
    pass


class CannotChangeSelfError(Exception):
    pass


class CannotAssignSuperAdminError(Exception):
    pass


@dataclass
class ChangeUserRoleCommand:
    user_id: str
    company_id: str
    current_user_id: str
    new_role: str


class ChangeUserRoleCommandHandler:
    def __init__(self, user_repo: UserRepositoryInterface):
        self.user_repo = user_repo

    def handle(self, command: ChangeUserRoleCommand) -> User:
        user = self.user_repo.find_by_id_and_company(command.user_id, command.company_id)
        if not user:
            raise UserNotFoundError("User not found")

        if command.user_id == command.current_user_id:
            raise CannotChangeSelfError("Cannot change your own role")

        new_role = UserRole(command.new_role)
        if new_role == UserRole.SUPER_ADMIN:
            raise CannotAssignSuperAdminError("Cannot assign super_admin role")

        user.change_role(new_role)
        self.user_repo.save(user)
        logger.info("User %s role changed to %s", user.id, new_role.value)
        return user
