from dataclasses import dataclass

from src.framework.application.command_bus import Command, CommandHandler
from src.sla_bc.sla.domain.exceptions import SlaPolicyNotFoundError
from src.sla_bc.sla.domain.repository import SlaRepositoryInterface


@dataclass
class DeactivateSlaPolicyCommand(Command):
    policy_id: str
    company_id: str


class DeactivateSlaPolicyCommandHandler(CommandHandler[DeactivateSlaPolicyCommand]):
    def __init__(self, sla_repo: SlaRepositoryInterface):
        self.sla_repo = sla_repo

    def handle(self, command: DeactivateSlaPolicyCommand) -> None:
        policy = self.sla_repo.find_policy_by_id(
            command.policy_id, command.company_id
        )
        if not policy:
            raise SlaPolicyNotFoundError(command.policy_id)

        policy.deactivate()
        self.sla_repo.save_policy(policy)
