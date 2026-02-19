from abc import ABC, abstractmethod
from typing import Optional

from src.company_bc.equipment_profile.domain.entities import (
    EquipmentProfile,
)


class EquipmentProfileRepositoryInterface(ABC):

    @abstractmethod
    def save(
        self, profile: EquipmentProfile,
    ) -> EquipmentProfile: ...

    @abstractmethod
    def find_by_id(
        self, profile_id: str, company_id: str,
    ) -> Optional[EquipmentProfile]: ...

    @abstractmethod
    def find_active(
        self,
        company_id: str,
        department_id: str,
        role: str,
    ) -> Optional[EquipmentProfile]: ...

    @abstractmethod
    def find_all(
        self,
        company_id: str,
        page: int,
        page_size: int,
        department_id: Optional[str] = None,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> tuple[list[EquipmentProfile], int]: ...

    @abstractmethod
    def delete(self, profile_id: str) -> None: ...
