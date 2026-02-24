from dataclasses import dataclass

from src.framework.application.command_bus import Command, CommandHandler
from src.sla_bc.sla.domain.entities import SlaBreachRecord
from src.sla_bc.sla.domain.enums import SlaBreachType
from src.sla_bc.sla.domain.repository import SlaRepositoryInterface


@dataclass
class RecordSlaBreachCommand(Command):
    company_id: str
    request_id: str
    policy_id: str
    breach_type: str
    target_hours: float
    actual_hours: float
    escalated: bool = False


class RecordSlaBreachCommandHandler(CommandHandler[RecordSlaBreachCommand]):
    def __init__(self, sla_repo: SlaRepositoryInterface):
        self.sla_repo = sla_repo

    def handle(self, command: RecordSlaBreachCommand) -> None:
        # Idempotent: skip if breach already recorded for this request+type
        if self.sla_repo.has_breach_of_type(
            command.request_id, command.breach_type
        ):
            return

        breach = SlaBreachRecord.create(
            company_id=command.company_id,
            request_id=command.request_id,
            policy_id=command.policy_id,
            breach_type=SlaBreachType(command.breach_type),
            target_hours=command.target_hours,
            actual_hours=command.actual_hours,
            escalated=command.escalated,
        )
        self.sla_repo.save_breach(breach)
