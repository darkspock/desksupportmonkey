from dataclasses import dataclass

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


class ProfileNotFoundError(Exception):
    pass


@dataclass
class GetEquipmentProfileQuery(Query):
    profile_id: str
    company_id: str


class GetEquipmentProfileQueryHandler(
    QueryHandler[
        GetEquipmentProfileQuery, EquipmentProfile,
    ],
):
    def __init__(
        self,
        profile_repo: EquipmentProfileRepositoryInterface,
    ):
        self.profile_repo = profile_repo

    def handle(
        self, query: GetEquipmentProfileQuery,
    ) -> EquipmentProfile:
        profile = self.profile_repo.find_by_id(
            query.profile_id, query.company_id,
        )
        if not profile:
            raise ProfileNotFoundError(
                "Equipment profile not found",
            )
        return profile
