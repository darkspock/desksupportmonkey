from dataclasses import dataclass
from datetime import date
from typing import Optional

from src.framework.application.command_bus import Command, CommandHandler
from src.risk_bc.risk.domain.entities import MitigationPlan, RiskHistory
from src.risk_bc.risk.domain.enums import RiskHistoryEventType
from src.risk_bc.risk.domain.exceptions import RiskClosedError, RiskNotFoundError
from src.risk_bc.risk.domain.repository import RiskRepositoryInterface


@dataclass
class AddMitigationCommand(Command):
    risk_id: str
    company_id: str
    actor_id: str
    mitigation_id: str
    description: str
    owner_id: Optional[str] = None
    target_date: Optional[date] = None


class AddMitigationCommandHandler(CommandHandler[AddMitigationCommand]):
    def __init__(self, risk_repo: RiskRepositoryInterface):
        self.risk_repo = risk_repo

    def handle(self, command: AddMitigationCommand) -> None:
        risk = self.risk_repo.find_by_id(command.risk_id, command.company_id)
        if not risk:
            raise RiskNotFoundError(command.risk_id)
        if risk.status.value == "closed":
            raise RiskClosedError()

        plan = MitigationPlan.create(
            risk_id=command.risk_id,
            description=command.description,
            owner_id=command.owner_id,
            target_date=command.target_date,
            id=command.mitigation_id,
        )
        self.risk_repo.save_mitigation(plan)

        self.risk_repo.add_history(
            RiskHistory.create(
                risk_id=command.risk_id,
                event_type=RiskHistoryEventType.MITIGATION_ADDED,
                description=f"Mitigation plan added: {command.description[:50]}",
                actor_id=command.actor_id,
                metadata={"mitigation_id": plan.id},
            )
        )
