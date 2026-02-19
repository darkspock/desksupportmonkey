import logging
from dataclasses import dataclass
from datetime import time
from typing import List

from src.appointment_bc.appointment.domain.entities import (
    TechnicianAvailability,
)
from src.appointment_bc.appointment.domain.repository import (
    TechnicianAvailabilityRepositoryInterface,
)
from src.framework.application.command_bus import (
    Command,
    CommandHandler,
)

logger = logging.getLogger(__name__)


@dataclass
class AvailabilityWindowInput:
    day_of_week: int
    start_time: time
    end_time: time


@dataclass
class SetAvailabilityCommand(Command):
    technician_id: str
    company_id: str
    windows: List[AvailabilityWindowInput]


class SetAvailabilityCommandHandler(
    CommandHandler[SetAvailabilityCommand],
):
    def __init__(
        self,
        availability_repo: TechnicianAvailabilityRepositoryInterface,
    ):
        self.availability_repo = availability_repo

    def handle(
        self, command: SetAvailabilityCommand,
    ) -> None:
        entities = [
            TechnicianAvailability.create(
                company_id=command.company_id,
                technician_id=command.technician_id,
                day_of_week=w.day_of_week,
                start_time=w.start_time,
                end_time=w.end_time,
            )
            for w in command.windows
        ]

        self.availability_repo.save_all(
            technician_id=command.technician_id,
            company_id=command.company_id,
            windows=entities,
        )

        logger.info(
            "Set %d availability windows for technician %s",
            len(entities),
            command.technician_id,
        )
