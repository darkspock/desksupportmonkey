import logging
from dataclasses import dataclass

from src.appointment_bc.appointment.domain.repository import (
    AvailabilityOverrideRepositoryInterface,
)
from src.framework.application.command_bus import (
    Command,
    CommandHandler,
)

logger = logging.getLogger(__name__)


class OverrideNotFoundError(Exception):
    pass


@dataclass
class DeleteOverrideCommand(Command):
    override_id: str
    company_id: str


class DeleteOverrideCommandHandler(
    CommandHandler[DeleteOverrideCommand],
):
    def __init__(
        self,
        override_repo: AvailabilityOverrideRepositoryInterface,
    ):
        self.override_repo = override_repo

    def handle(
        self, command: DeleteOverrideCommand,
    ) -> None:
        deleted = self.override_repo.delete(
            command.override_id, command.company_id,
        )
        if not deleted:
            raise OverrideNotFoundError(
                f"Override {command.override_id} not found"
            )

        logger.info(
            "Deleted availability override %s",
            command.override_id,
        )
