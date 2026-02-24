from dataclasses import dataclass
from typing import Optional

from src.framework.application.command_bus import Command, CommandHandler
from src.sla_bc.sla.domain.exceptions import SlaPolicyNotFoundError
from src.sla_bc.sla.domain.repository import SlaRepositoryInterface


@dataclass
class UpdateSlaPolicyCommand(Command):
    policy_id: str
    company_id: str
    name: Optional[str] = None
    response_time_hours: Optional[float] = None
    resolution_time_hours: Optional[float] = None
    warning_threshold_pct: Optional[int] = None
    escalate_on_breach: Optional[bool] = None


class UpdateSlaPolicyCommandHandler(CommandHandler[UpdateSlaPolicyCommand]):
    def __init__(self, sla_repo: SlaRepositoryInterface):
        self.sla_repo = sla_repo

    def handle(self, command: UpdateSlaPolicyCommand) -> None:
        policy = self.sla_repo.find_policy_by_id(
            command.policy_id, command.company_id
        )
        if not policy:
            raise SlaPolicyNotFoundError(command.policy_id)

        policy.update(
            name=command.name,
            response_time_hours=command.response_time_hours,
            resolution_time_hours=command.resolution_time_hours,
            warning_threshold_pct=command.warning_threshold_pct,
            escalate_on_breach=command.escalate_on_breach,
        )
        self.sla_repo.save_policy(policy)
