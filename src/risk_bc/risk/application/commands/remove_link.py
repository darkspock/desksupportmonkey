from dataclasses import dataclass

from src.framework.application.command_bus import Command, CommandHandler
from src.risk_bc.risk.domain.entities import RiskHistory
from src.risk_bc.risk.domain.enums import RiskHistoryEventType
from src.risk_bc.risk.domain.exceptions import (
    LinkNotFoundError,
    RiskNotFoundError,
)
from src.risk_bc.risk.domain.repository import RiskRepositoryInterface


@dataclass
class RemoveLinkCommand(Command):
    risk_id: str
    company_id: str
    actor_id: str
    link_id: str


class RemoveLinkCommandHandler(CommandHandler[RemoveLinkCommand]):
    def __init__(self, risk_repo: RiskRepositoryInterface):
        self.risk_repo = risk_repo

    def handle(self, command: RemoveLinkCommand) -> None:
        risk = self.risk_repo.find_by_id(command.risk_id, command.company_id)
        if not risk:
            raise RiskNotFoundError(command.risk_id)

        links = self.risk_repo.get_links(command.risk_id)
        found = None
        for lnk in links:
            if lnk.id == command.link_id:
                found = lnk
                break

        if not found:
            raise LinkNotFoundError(command.link_id)

        self.risk_repo.delete_link(command.link_id, command.risk_id)

        self.risk_repo.add_history(
            RiskHistory.create(
                risk_id=command.risk_id,
                event_type=RiskHistoryEventType.LINK_REMOVED,
                description=f"Removed link to {found.link_type.value}: {found.link_id}",
                actor_id=command.actor_id,
                metadata={
                    "link_type": found.link_type.value,
                    "link_id": found.link_id,
                },
            )
        )
