import logging
from dataclasses import dataclass

from src.company_bc.equipment_profile.domain.repository import (
    EquipmentProfileRepositoryInterface,
)
from src.framework.application.command_bus import (
    Command,
    CommandHandler,
)

logger = logging.getLogger(__name__)


class ProfileNotFoundError(Exception):
    pass


@dataclass
class DeactivateEquipmentProfileCommand(Command):
    profile_id: str
    company_id: str
    performed_by: str = ""


class DeactivateEquipmentProfileCommandHandler(
    CommandHandler[DeactivateEquipmentProfileCommand],
):
    def __init__(
        self,
        profile_repo: EquipmentProfileRepositoryInterface,
    ):
        self.profile_repo = profile_repo

    def handle(
        self,
        command: DeactivateEquipmentProfileCommand,
    ) -> None:
        profile = self.profile_repo.find_by_id(
            command.profile_id, command.company_id,
        )
        if not profile:
            raise ProfileNotFoundError(
                "Equipment profile not found",
            )

        profile.deactivate()
        self.profile_repo.save(profile)
        logger.info(
            "Equipment profile %s deactivated",
            command.profile_id,
        )
