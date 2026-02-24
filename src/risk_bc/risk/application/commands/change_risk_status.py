from dataclasses import dataclass

from src.framework.application.command_bus import Command, CommandHandler
from src.risk_bc.risk.domain.entities import RiskHistory
from src.risk_bc.risk.domain.enums import RiskHistoryEventType, RiskStatus
from src.risk_bc.risk.domain.exceptions import RiskNotFoundError
from src.risk_bc.risk.domain.repository import RiskRepositoryInterface


@dataclass
class ChangeRiskStatusCommand(Command):
    risk_id: str
    company_id: str
    actor_id: str
    new_status: str


class ChangeRiskStatusCommandHandler(CommandHandler[ChangeRiskStatusCommand]):
    def __init__(self, risk_repo: RiskRepositoryInterface):
        self.risk_repo = risk_repo

    def handle(self, command: ChangeRiskStatusCommand) -> None:
        risk = self.risk_repo.find_by_id(command.risk_id, command.company_id)
        if not risk:
            raise RiskNotFoundError(command.risk_id)

        old_status = risk.status.value
        new_status = RiskStatus(command.new_status)
        risk.change_status(new_status)
        self.risk_repo.save(risk)

        self.risk_repo.add_history(
            RiskHistory.create(
                risk_id=risk.id,
                event_type=RiskHistoryEventType.STATUS_CHANGED,
                description=f"Status changed: {old_status} → {new_status.value}",
                actor_id=command.actor_id,
                metadata={
                    "old_status": old_status,
                    "new_status": new_status.value,
                },
            )
        )
