from dataclasses import dataclass

from src.framework.application.command_bus import Command, CommandHandler
from src.risk_bc.risk.domain.entities import RiskHistory
from src.risk_bc.risk.domain.enums import RiskHistoryEventType
from src.risk_bc.risk.domain.exceptions import RiskNotFoundError
from src.risk_bc.risk.domain.repository import RiskRepositoryInterface


@dataclass
class AssessRiskCommand(Command):
    risk_id: str
    company_id: str
    actor_id: str
    likelihood: int
    impact: int


class AssessRiskCommandHandler(CommandHandler[AssessRiskCommand]):
    def __init__(self, risk_repo: RiskRepositoryInterface):
        self.risk_repo = risk_repo

    def handle(self, command: AssessRiskCommand) -> None:
        risk = self.risk_repo.find_by_id(command.risk_id, command.company_id)
        if not risk:
            raise RiskNotFoundError(command.risk_id)

        old_likelihood = risk.likelihood
        old_impact = risk.impact
        old_level = risk.risk_level.value if risk.risk_level else None

        risk.assess(command.likelihood, command.impact)
        self.risk_repo.save(risk)

        self.risk_repo.add_history(
            RiskHistory.create(
                risk_id=risk.id,
                event_type=RiskHistoryEventType.SCORE_CHANGED,
                description=(
                    f"Risk assessed: L{command.likelihood}×I{command.impact} "
                    f"= {risk.risk_level.value if risk.risk_level else 'N/A'}"
                ),
                actor_id=command.actor_id,
                metadata={
                    "old_likelihood": old_likelihood,
                    "old_impact": old_impact,
                    "old_level": old_level,
                    "new_likelihood": command.likelihood,
                    "new_impact": command.impact,
                    "new_level": risk.risk_level.value if risk.risk_level else None,
                },
            )
        )
