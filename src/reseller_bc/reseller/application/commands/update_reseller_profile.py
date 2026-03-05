from dataclasses import dataclass
from typing import Optional

from src.framework.application.command_bus import Command, CommandHandler
from src.reseller_bc.reseller.domain.exceptions import ResellerNotFoundException
from src.reseller_bc.reseller.domain.repository import ResellerRepositoryInterface


@dataclass
class UpdateResellerProfileCommand(Command):
    reseller_id: str
    company_name: Optional[str] = None
    tax_id: Optional[str] = None


class UpdateResellerProfileCommandHandler(CommandHandler[UpdateResellerProfileCommand]):
    def __init__(self, repo: ResellerRepositoryInterface):
        self.repo = repo

    def handle(self, command: UpdateResellerProfileCommand) -> None:
        reseller = self.repo.get_by_id(command.reseller_id)
        if reseller is None:
            raise ResellerNotFoundException(command.reseller_id)

        reseller.update_profile(
            company_name=command.company_name,
            tax_id=command.tax_id,
        )
        self.repo.save(reseller)
