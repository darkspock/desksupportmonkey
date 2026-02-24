from dataclasses import dataclass

from src.framework.application.command_bus import Command, CommandHandler
from src.risk_bc.risk.domain.entities import RiskHistory
from src.risk_bc.risk.domain.enums import RiskHistoryEventType, RiskTreatment
from src.risk_bc.risk.domain.exceptions import RiskNotFoundError
from src.risk_bc.risk.domain.repository import RiskRepositoryInterface


@dataclass
class SetTreatmentCommand(Command):
    risk_id: str
    company_id: str
    actor_id: str
    treatment: str


class SetTreatmentCommandHandler(CommandHandler[SetTreatmentCommand]):
    def __init__(self, risk_repo: RiskRepositoryInterface):
        self.risk_repo = risk_repo

    def handle(self, command: SetTreatmentCommand) -> None:
        risk = self.risk_repo.find_by_id(command.risk_id, command.company_id)
        if not risk:
            raise RiskNotFoundError(command.risk_id)

        old_treatment = risk.treatment.value if risk.treatment else None
        new_treatment = RiskTreatment(command.treatment)
        risk.set_treatment(new_treatment)
        self.risk_repo.save(risk)

        self.risk_repo.add_history(
            RiskHistory.create(
                risk_id=risk.id,
                event_type=RiskHistoryEventType.TREATMENT_CHANGED,
                description=f"Treatment set to {new_treatment.value}",
                actor_id=command.actor_id,
                metadata={
                    "old_treatment": old_treatment,
                    "new_treatment": new_treatment.value,
                },
            )
        )
