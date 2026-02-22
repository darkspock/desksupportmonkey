import logging
from dataclasses import dataclass, field
from typing import Optional

import ulid

from src.asset_bc.asset.domain.enums import AssetType
from src.company_bc.equipment_profile.domain.entities import (
    EquipmentProfile,
    EquipmentProfileItem,
)
from src.company_bc.equipment_profile.domain.repository import (
    EquipmentProfileRepositoryInterface,
)
from src.framework.application.command_bus import (
    Command,
    CommandHandler,
)

logger = logging.getLogger(__name__)


class ActiveProfileExistsError(Exception):
    pass


@dataclass
class ProfileItemInput:
    asset_type: AssetType
    quantity: int = 1
    preferred_brand: Optional[str] = None
    preferred_model: Optional[str] = None
    min_ram_gb: Optional[int] = None
    min_storage_gb: Optional[int] = None
    budget_cents: Optional[int] = None


@dataclass
class CreateEquipmentProfileCommand(Command):
    company_id: str
    department_id: str
    employee_role_id: str
    items: list[ProfileItemInput] = field(
        default_factory=list,
    )
    id: str = ""
    performed_by: str = ""


class CreateEquipmentProfileCommandHandler(
    CommandHandler[CreateEquipmentProfileCommand],
):
    def __init__(
        self,
        profile_repo: EquipmentProfileRepositoryInterface,
    ):
        self.profile_repo = profile_repo

    def handle(
        self, command: CreateEquipmentProfileCommand,
    ) -> None:
        existing = self.profile_repo.find_active(
            company_id=command.company_id,
            department_id=command.department_id,
            employee_role_id=command.employee_role_id,
        )
        if existing:
            raise ActiveProfileExistsError(
                "An active profile already exists "
                "for this department and employee role",
            )

        profile_id = command.id or str(ulid.new())
        profile = EquipmentProfile.create(
            id=profile_id,
            company_id=command.company_id,
            department_id=command.department_id,
            employee_role_id=command.employee_role_id,
        )
        profile.items = [
            EquipmentProfileItem(
                id=str(ulid.new()),
                profile_id=profile_id,
                asset_type=item.asset_type,
                quantity=item.quantity,
                preferred_brand=item.preferred_brand,
                preferred_model=item.preferred_model,
                min_ram_gb=item.min_ram_gb,
                min_storage_gb=item.min_storage_gb,
                budget_cents=item.budget_cents,
            )
            for item in command.items
        ]
        self.profile_repo.save(profile)
        logger.info(
            "Equipment profile %s created for "
            "department %s employee_role %s",
            profile_id,
            command.department_id,
            command.employee_role_id,
        )
