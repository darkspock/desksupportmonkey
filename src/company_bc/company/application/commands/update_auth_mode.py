from dataclasses import dataclass

from src.auth_bc.company_user.domain.repository import CompanyUserRepositoryInterface
from src.company_bc.company.domain.entities import NoAdminMembershipError
from src.company_bc.company.domain.enums import AuthMode
from src.company_bc.company.domain.repository import CompanyRepositoryInterface
from src.framework.application.command_bus import Command, CommandHandler


@dataclass
class UpdateAuthModeCommand(Command):
    company_id: str
    auth_mode: str


class UpdateAuthModeCommandHandler(CommandHandler[UpdateAuthModeCommand]):
    def __init__(
        self,
        company_repo: CompanyRepositoryInterface,
        company_user_repo: CompanyUserRepositoryInterface,
    ):
        self.company_repo = company_repo
        self.company_user_repo = company_user_repo

    def handle(self, command: UpdateAuthModeCommand) -> None:
        company = self.company_repo.find_by_id(command.company_id)
        if not company:
            raise ValueError("Company not found")

        try:
            new_mode = AuthMode(command.auth_mode)
        except ValueError:
            raise ValueError(f"Invalid auth mode: '{command.auth_mode}'")

        if new_mode == AuthMode.MEMBERSHIP_ONLY:
            admin_count = self.company_user_repo.count_admins_in_company(command.company_id)
            if admin_count == 0:
                raise NoAdminMembershipError(
                    "Cannot switch to membership_only: no admin memberships found"
                )

        company.set_auth_mode(new_mode)
        self.company_repo.save(company)
