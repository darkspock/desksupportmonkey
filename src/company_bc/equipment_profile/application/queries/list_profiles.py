from dataclasses import dataclass
from typing import Optional

from src.company_bc.equipment_profile.domain.entities import (
    EquipmentProfile,
)
from src.company_bc.equipment_profile.domain.repository import (
    EquipmentProfileRepositoryInterface,
)
from src.framework.application.query_bus import (
    Query,
    QueryHandler,
)


@dataclass
class ListEquipmentProfilesQuery(Query):
    company_id: str
    page: int = 1
    page_size: int = 20
    department_id: Optional[str] = None
    employee_role_id: Optional[str] = None
    is_active: Optional[bool] = None


class ListEquipmentProfilesQueryHandler(
    QueryHandler[
        ListEquipmentProfilesQuery,
        tuple[list[EquipmentProfile], int],
    ],
):
    def __init__(
        self,
        profile_repo: EquipmentProfileRepositoryInterface,
    ):
        self.profile_repo = profile_repo

    def handle(
        self, query: ListEquipmentProfilesQuery,
    ) -> tuple[list[EquipmentProfile], int]:
        return self.profile_repo.find_all(
            company_id=query.company_id,
            page=query.page,
            page_size=query.page_size,
            department_id=query.department_id,
            employee_role_id=query.employee_role_id,
            is_active=query.is_active,
        )
