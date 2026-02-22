import logging
from dataclasses import dataclass, field
from typing import Optional

import ulid

from src.asset_bc.asset.domain.enums import AssetType
from src.company_bc.equipment_profile.domain.entities import (
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


class ProfileNotFoundError(Exception):
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
class UpdateEquipmentProfileCommand(Command):
    profile_id: str
    company_id: str
    items: list[ProfileItemInput] = field(
        default_factory=list,
    )
    performed_by: str = ""


class UpdateEquipmentProfileCommandHandler(
    CommandHandler[UpdateEquipmentProfileCommand],
):
    def __init__(
        self,
        profile_repo: EquipmentProfileRepositoryInterface,
    ):
        self.profile_repo = profile_repo

    def handle(
        self, command: UpdateEquipmentProfileCommand,
    ) -> None:
        profile = self.profile_repo.find_by_id(
            command.profile_id, command.company_id,
        )
        if not profile:
            raise ProfileNotFoundError(
                "Equipment profile not found",
            )

        profile.items = [
            EquipmentProfileItem(
                id=str(ulid.new()),
                profile_id=profile.id,
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
            "Equipment profile %s updated",
            command.profile_id,
        )
