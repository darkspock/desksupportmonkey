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
class ActivateEquipmentProfileCommand(Command):
    profile_id: str
    company_id: str
    performed_by: str = ""


class ActivateEquipmentProfileCommandHandler(
    CommandHandler[ActivateEquipmentProfileCommand],
):
    def __init__(
        self,
        profile_repo: EquipmentProfileRepositoryInterface,
    ):
        self.profile_repo = profile_repo

    def handle(
        self, command: ActivateEquipmentProfileCommand,
    ) -> None:
        profile = self.profile_repo.find_by_id(
            command.profile_id, command.company_id,
        )
        if not profile:
            raise ProfileNotFoundError(
                "Equipment profile not found",
            )

        # Deactivate any existing active profile
        # for the same department+employee_role
        conflicting = self.profile_repo.find_active(
            company_id=profile.company_id,
            department_id=profile.department_id,
            employee_role_id=profile.employee_role_id,
        )
        if conflicting and conflicting.id != profile.id:
            conflicting.deactivate()
            self.profile_repo.save(conflicting)

        profile.activate()
        self.profile_repo.save(profile)
        logger.info(
            "Equipment profile %s activated",
            command.profile_id,
        )
