from dataclasses import dataclass

from src.framework.application.command_bus import Command, CommandHandler
from src.risk_bc.risk.domain.entities import RiskHistory
from src.risk_bc.risk.domain.enums import RiskHistoryEventType
from src.risk_bc.risk.domain.exceptions import (
    MitigationNotFoundError,
    RiskNotFoundError,
)
from src.risk_bc.risk.domain.repository import RiskRepositoryInterface


@dataclass
class DeleteMitigationCommand(Command):
    risk_id: str
    company_id: str
    actor_id: str
    mitigation_id: str


class DeleteMitigationCommandHandler(CommandHandler[DeleteMitigationCommand]):
    def __init__(self, risk_repo: RiskRepositoryInterface):
        self.risk_repo = risk_repo

    def handle(self, command: DeleteMitigationCommand) -> None:
        risk = self.risk_repo.find_by_id(command.risk_id, command.company_id)
        if not risk:
            raise RiskNotFoundError(command.risk_id)

        mit = self.risk_repo.find_mitigation_by_id(
            command.mitigation_id, command.risk_id
        )
        if not mit:
            raise MitigationNotFoundError(command.mitigation_id)

        self.risk_repo.delete_mitigation(command.mitigation_id, command.risk_id)

        self.risk_repo.add_history(
            RiskHistory.create(
                risk_id=command.risk_id,
                event_type=RiskHistoryEventType.MITIGATION_DELETED,
                description=f"Mitigation plan deleted: {mit.description[:50]}",
                actor_id=command.actor_id,
                metadata={"mitigation_id": mit.id},
            )
        )
