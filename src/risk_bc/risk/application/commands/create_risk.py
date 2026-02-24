from dataclasses import dataclass
from typing import Optional

from src.framework.application.command_bus import Command, CommandHandler
from src.risk_bc.risk.domain.entities import Risk, RiskHistory
from src.risk_bc.risk.domain.enums import RiskCategory, RiskHistoryEventType
from src.risk_bc.risk.domain.repository import RiskRepositoryInterface


@dataclass
class CreateRiskCommand(Command):
    risk_id: str
    company_id: str
    title: str
    description: str
    category: str
    created_by: str
    owner_id: Optional[str] = None


class CreateRiskCommandHandler(CommandHandler[CreateRiskCommand]):
    def __init__(self, risk_repo: RiskRepositoryInterface):
        self.risk_repo = risk_repo

    def handle(self, command: CreateRiskCommand) -> None:
        cat = RiskCategory(command.category)
        risk = Risk.create(
            company_id=command.company_id,
            title=command.title,
            description=command.description,
            category=cat,
            created_by=command.created_by,
            owner_id=command.owner_id,
            id=command.risk_id,
        )
        self.risk_repo.save(risk)

        history = RiskHistory.create(
            risk_id=risk.id,
            event_type=RiskHistoryEventType.CREATED,
            description=f"Risk created: {risk.title}",
            actor_id=command.created_by,
            metadata={"category": cat.value},
        )
        self.risk_repo.add_history(history)
