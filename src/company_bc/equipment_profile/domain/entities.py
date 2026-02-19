from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import ulid

from src.asset_bc.asset.domain.enums import AssetType
from src.auth_bc.user.domain.enums import UserRole


@dataclass
class EquipmentProfileItem:
    id: str
    profile_id: str
    asset_type: AssetType
    quantity: int = 1
    preferred_brand: Optional[str] = None
    preferred_model: Optional[str] = None
    min_ram_gb: Optional[int] = None
    min_storage_gb: Optional[int] = None


@dataclass
class EquipmentProfile:
    id: str
    company_id: str
    department_id: str
    role: UserRole
    is_active: bool = True
    items: list[EquipmentProfileItem] = field(
        default_factory=list,
    )
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        company_id: str,
        department_id: str,
        role: UserRole,
        id: Optional[str] = None,
    ) -> "EquipmentProfile":
        return cls(
            id=id or str(ulid.new()),
            company_id=company_id,
            department_id=department_id,
            role=role,
            is_active=True,
        )

    def activate(self) -> None:
        self.is_active = True

    def deactivate(self) -> None:
        self.is_active = False
