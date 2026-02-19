import logging
from dataclasses import dataclass
from datetime import date, time
from typing import Optional

from src.appointment_bc.appointment.domain.entities import (
    AvailabilityOverride,
)
from src.appointment_bc.appointment.domain.repository import (
    AvailabilityOverrideRepositoryInterface,
)
from src.framework.application.command_bus import (
    Command,
    CommandHandler,
)

logger = logging.getLogger(__name__)


@dataclass
class AddOverrideCommand(Command):
    override_id: str
    company_id: str
    technician_id: str
    target_date: date
    is_available: bool
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    reason: Optional[str] = None


class AddOverrideCommandHandler(
    CommandHandler[AddOverrideCommand],
):
    def __init__(
        self,
        override_repo: AvailabilityOverrideRepositoryInterface,
    ):
        self.override_repo = override_repo

    def handle(
        self, command: AddOverrideCommand,
    ) -> None:
        override = AvailabilityOverride.create(
            company_id=command.company_id,
            technician_id=command.technician_id,
            target_date=command.target_date,
            is_available=command.is_available,
            start_time=command.start_time,
            end_time=command.end_time,
            reason=command.reason,
            id=command.override_id,
        )

        self.override_repo.save(override)

        logger.info(
            "Added availability override %s for technician %s on %s",
            override.id,
            command.technician_id,
            command.target_date,
        )
