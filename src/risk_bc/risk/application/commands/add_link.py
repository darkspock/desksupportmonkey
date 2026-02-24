from dataclasses import dataclass

from src.framework.application.command_bus import Command, CommandHandler
from src.risk_bc.risk.domain.entities import RiskHistory, RiskLink
from src.risk_bc.risk.domain.enums import RiskHistoryEventType, RiskLinkType
from src.risk_bc.risk.domain.exceptions import (
    DuplicateLinkError,
    RiskClosedError,
    RiskNotFoundError,
)
from src.risk_bc.risk.domain.repository import RiskRepositoryInterface


@dataclass
class AddLinkCommand(Command):
    risk_id: str
    company_id: str
    actor_id: str
    link_id: str
    link_type: str
    entity_id: str


class AddLinkCommandHandler(CommandHandler[AddLinkCommand]):
    def __init__(self, risk_repo: RiskRepositoryInterface):
        self.risk_repo = risk_repo

    def handle(self, command: AddLinkCommand) -> None:
        risk = self.risk_repo.find_by_id(command.risk_id, command.company_id)
        if not risk:
            raise RiskNotFoundError(command.risk_id)
        if risk.status.value == "closed":
            raise RiskClosedError()

        link_type = RiskLinkType(command.link_type)

        # Check for duplicate
        existing_links = self.risk_repo.get_links(command.risk_id)
        for lnk in existing_links:
            if lnk.link_type == link_type and lnk.link_id == command.entity_id:
                raise DuplicateLinkError(link_type.value, command.entity_id)

        link = RiskLink.create(
            risk_id=command.risk_id,
            link_type=link_type,
            link_id=command.entity_id,
            id=command.link_id,
        )
        self.risk_repo.add_link(link)

        self.risk_repo.add_history(
            RiskHistory.create(
                risk_id=command.risk_id,
                event_type=RiskHistoryEventType.LINK_ADDED,
                description=f"Linked to {link_type.value}: {command.entity_id}",
                actor_id=command.actor_id,
                metadata={
                    "link_type": link_type.value,
                    "link_id": command.entity_id,
                },
            )
        )
