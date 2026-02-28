from dataclasses import dataclass

from src.company_bc.sla_escalation_config.domain.entities import (
    CompanySlaEscalationConfig,
)
from src.company_bc.sla_escalation_config.domain.repository import (
    SlaEscalationConfigRepositoryInterface,
)
from src.framework.application.command_bus import Command, CommandHandler


@dataclass
class SaveSlaEscalationConfigCommand(Command):
    company_id: str
    enabled: bool
    performed_by: str


class SaveSlaEscalationConfigCommandHandler(
    CommandHandler[SaveSlaEscalationConfigCommand],
):
    def __init__(
        self,
        config_repo: SlaEscalationConfigRepositoryInterface,
    ):
        self.config_repo = config_repo

    def handle(self, command: SaveSlaEscalationConfigCommand) -> None:
        existing = self.config_repo.find_by_company(command.company_id)
        if existing:
            existing.enabled = command.enabled
            self.config_repo.save(existing)
        else:
            config = CompanySlaEscalationConfig.create(
                company_id=command.company_id,
                enabled=command.enabled,
            )
            self.config_repo.save(config)
