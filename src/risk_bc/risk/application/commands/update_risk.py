from dataclasses import dataclass
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
from typing import Optional

from src.framework.application.command_bus import Command, CommandHandler
from src.risk_bc.risk.domain.entities import RiskHistory
from src.risk_bc.risk.domain.enums import (
    ReviewCadence,
    RiskCategory,
    RiskHistoryEventType,
)
from src.risk_bc.risk.domain.exceptions import RiskNotFoundError
from src.risk_bc.risk.domain.repository import RiskRepositoryInterface


CADENCE_DELTAS = {
    ReviewCadence.MONTHLY: relativedelta(months=1),
    ReviewCadence.QUARTERLY: relativedelta(months=3),
    ReviewCadence.ANNUALLY: relativedelta(years=1),
}


@dataclass
class UpdateRiskCommand(Command):
    risk_id: str
    company_id: str
    actor_id: str
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    owner_id: Optional[str] = None
    review_cadence: Optional[str] = None


class UpdateRiskCommandHandler(CommandHandler[UpdateRiskCommand]):
    def __init__(self, risk_repo: RiskRepositoryInterface):
        self.risk_repo = risk_repo

    def handle(self, command: UpdateRiskCommand) -> None:
        risk = self.risk_repo.find_by_id(command.risk_id, command.company_id)
        if not risk:
            raise RiskNotFoundError(command.risk_id)

        cat = RiskCategory(command.category) if command.category else None
        cadence = (
            ReviewCadence(command.review_cadence)
            if command.review_cadence
            else None
        )

        old_owner = risk.owner_id
        risk.update_details(
            title=command.title,
            description=command.description,
            category=cat,
            owner_id=command.owner_id,
            review_cadence=cadence,
        )

        if cadence:
            now = datetime.now(timezone.utc)
            delta = CADENCE_DELTAS[cadence]
            risk.next_review_at = now + delta

        self.risk_repo.save(risk)

        changes: dict = {}
        if command.title:
            changes["title"] = command.title
        if command.description:
            changes["description"] = "(updated)"
        if cat:
            changes["category"] = cat.value
        if cadence:
            changes["review_cadence"] = cadence.value

        self.risk_repo.add_history(
            RiskHistory.create(
                risk_id=risk.id,
                event_type=RiskHistoryEventType.UPDATED,
                description="Risk updated",
                actor_id=command.actor_id,
                metadata=changes if changes else None,
            )
        )

        if command.owner_id and command.owner_id != old_owner:
            self.risk_repo.add_history(
                RiskHistory.create(
                    risk_id=risk.id,
                    event_type=RiskHistoryEventType.OWNER_CHANGED,
                    description="Risk owner changed",
                    actor_id=command.actor_id,
                    metadata={
                        "old_owner": old_owner,
                        "new_owner": command.owner_id,
                    },
                )
            )
