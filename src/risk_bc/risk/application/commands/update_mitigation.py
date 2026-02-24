from dataclasses import dataclass
from datetime import date
from typing import Optional

from src.framework.application.command_bus import Command, CommandHandler
from src.risk_bc.risk.domain.entities import RiskHistory
from src.risk_bc.risk.domain.enums import MitigationStatus, RiskHistoryEventType
from src.risk_bc.risk.domain.exceptions import (
    MitigationNotFoundError,
    RiskClosedError,
    RiskNotFoundError,
)
from src.risk_bc.risk.domain.repository import RiskRepositoryInterface


@dataclass
class UpdateMitigationCommand(Command):
    risk_id: str
    company_id: str
    actor_id: str
    mitigation_id: str
    description: Optional[str] = None
    status: Optional[str] = None
    owner_id: Optional[str] = None
    target_date: Optional[date] = None


class UpdateMitigationCommandHandler(CommandHandler[UpdateMitigationCommand]):
    def __init__(self, risk_repo: RiskRepositoryInterface):
        self.risk_repo = risk_repo

    def handle(self, command: UpdateMitigationCommand) -> None:
        risk = self.risk_repo.find_by_id(command.risk_id, command.company_id)
        if not risk:
            raise RiskNotFoundError(command.risk_id)
        if risk.status.value == "closed":
            raise RiskClosedError()

        mit = self.risk_repo.find_mitigation_by_id(
            command.mitigation_id, command.risk_id
        )
        if not mit:
            raise MitigationNotFoundError(command.mitigation_id)

        old_status = mit.status.value
        if command.description:
            mit.description = command.description.strip()
        if command.status:
            mit.update_status(MitigationStatus(command.status))
        if command.owner_id is not None:
            mit.owner_id = command.owner_id
        if command.target_date is not None:
            mit.target_date = command.target_date

        self.risk_repo.save_mitigation(mit)

        metadata: dict = {"mitigation_id": mit.id}
        if command.status and command.status != old_status:
            metadata["old_status"] = old_status
            metadata["new_status"] = command.status

        self.risk_repo.add_history(
            RiskHistory.create(
                risk_id=command.risk_id,
                event_type=RiskHistoryEventType.MITIGATION_UPDATED,
                description=f"Mitigation plan updated",
                actor_id=command.actor_id,
                metadata=metadata,
            )
        )
