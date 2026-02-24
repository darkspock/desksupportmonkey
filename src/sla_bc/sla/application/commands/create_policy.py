from dataclasses import dataclass
from typing import Optional

from src.framework.application.command_bus import Command, CommandHandler
from src.sla_bc.sla.domain.entities import SlaPolicy
from src.sla_bc.sla.domain.exceptions import DuplicateSlaPolicyError
from src.sla_bc.sla.domain.repository import SlaRepositoryInterface


@dataclass
class CreateSlaPolicyCommand(Command):
    policy_id: str
    company_id: str
    name: str
    priority: str
    response_time_hours: float
    resolution_time_hours: float
    request_type: Optional[str] = None
    warning_threshold_pct: int = 75
    escalate_on_breach: bool = False


class CreateSlaPolicyCommandHandler(CommandHandler[CreateSlaPolicyCommand]):
    def __init__(self, sla_repo: SlaRepositoryInterface):
        self.sla_repo = sla_repo

    def handle(self, command: CreateSlaPolicyCommand) -> None:
        # Check for duplicate active policy at same scope
        existing = self.sla_repo.find_active_policy_by_scope(
            company_id=command.company_id,
            priority=command.priority,
            request_type=command.request_type,
        )
        if existing:
            raise DuplicateSlaPolicyError(command.priority, command.request_type)

        policy = SlaPolicy.create(
            company_id=command.company_id,
            name=command.name,
            priority=command.priority,
            response_time_hours=command.response_time_hours,
            resolution_time_hours=command.resolution_time_hours,
            request_type=command.request_type,
            warning_threshold_pct=command.warning_threshold_pct,
            escalate_on_breach=command.escalate_on_breach,
        )
        policy.id = command.policy_id
        self.sla_repo.save_policy(policy)
