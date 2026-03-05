import logging
from dataclasses import dataclass
from typing import Optional

from core.email import EmailServiceInterface, send_admin_promotion_email
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
from src.auth_bc.user.domain.repository import UserRepositoryInterface
from src.framework.application.command_bus import Command, CommandHandler

logger = logging.getLogger(__name__)


class UserNotFoundError(Exception):
    pass


class CannotChangeSelfError(Exception):
    pass


class CannotAssignSuperAdminError(Exception):
    pass


class LastAdminError(Exception):
    pass


@dataclass
class ChangeUserRoleCommand(Command):
    user_id: str
    company_id: str
    current_user_id: str
    new_role: str


class ChangeUserRoleCommandHandler(CommandHandler[ChangeUserRoleCommand]):
    def __init__(
        self,
        user_repo: UserRepositoryInterface,
        email_service: Optional[EmailServiceInterface] = None,
    ):
        self.user_repo = user_repo
        self.email_service = email_service

    def handle(self, command: ChangeUserRoleCommand) -> None:
        user = self.user_repo.find_by_id_and_company(command.user_id, command.company_id)
        if not user:
            raise UserNotFoundError("User not found")

        new_role = UserRole(command.new_role)
        if user.role == new_role:
            return

        if command.user_id == command.current_user_id:
            raise CannotChangeSelfError("Cannot change your own role")

        if new_role == UserRole.SUPER_ADMIN:
            raise CannotAssignSuperAdminError("Cannot assign super_admin role")

        old_role = user.role

        # Last-admin protection: cannot demote the only admin
        if old_role == UserRole.ADMIN and new_role != UserRole.ADMIN:
            admin_count = self.user_repo.count_admins_by_company(command.company_id)
            if admin_count <= 1:
                raise LastAdminError("At least one admin must remain in the company")

        user.change_role(new_role)
        self.user_repo.save(user)

        logger.info("User %s role changed to %s", user.id, new_role.value)

        # Send notification emails when promoting to admin
        if new_role == UserRole.ADMIN and old_role != UserRole.ADMIN and self.email_service:
            try:
                admins = self.user_repo.find_admins_by_company(command.company_id)
                for admin in admins:
                    if admin.id != user.id:
                        send_admin_promotion_email(
                            self.email_service, admin.email, user.email, command.company_id
                        )
            except Exception:
                logger.exception("Failed to send admin promotion notification emails")
