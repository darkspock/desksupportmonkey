from dataclasses import dataclass

from src.framework.application.command_bus import Command, CommandHandler
from src.risk_bc.risk.domain.exceptions import RiskNotFoundError
from src.risk_bc.risk.domain.repository import RiskRepositoryInterface


@dataclass
class DeleteRiskCommand(Command):
    risk_id: str
    company_id: str


class DeleteRiskCommandHandler(CommandHandler[DeleteRiskCommand]):
    def __init__(self, risk_repo: RiskRepositoryInterface):
        self.risk_repo = risk_repo

    def handle(self, command: DeleteRiskCommand) -> None:
        risk = self.risk_repo.find_by_id(command.risk_id, command.company_id)
        if not risk:
            raise RiskNotFoundError(command.risk_id)
        self.risk_repo.delete(command.risk_id, command.company_id)
