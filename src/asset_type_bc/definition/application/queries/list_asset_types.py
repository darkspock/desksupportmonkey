from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from src.framework.application.query_bus import Query, QueryHandler
from src.asset_type_bc.definition.domain.repository import (
    AssetTypeDefinitionRepositoryInterface,
)


@dataclass
class AssetTypeDto:
    id: str
    company_id: str
    code: str
    name: str
    icon: Optional[str]
    is_active: bool
    sort_order: int
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


@dataclass
class ListAssetTypesQuery(Query):
    company_id: str
    active_only: bool = False


class ListAssetTypesQueryHandler(
    QueryHandler[ListAssetTypesQuery, list[AssetTypeDto]]
):
    def __init__(
        self, repo: AssetTypeDefinitionRepositoryInterface
    ):
        self.repo = repo

    def handle(
        self, query: ListAssetTypesQuery
    ) -> list[AssetTypeDto]:
        if query.active_only:
            definitions = self.repo.find_active(query.company_id)
        else:
            definitions = self.repo.find_all(query.company_id)
        return [
            AssetTypeDto(
                id=d.id,
                company_id=d.company_id,
                code=d.code,
                name=d.name,
                icon=d.icon,
                is_active=d.is_active,
                sort_order=d.sort_order,
                created_at=d.created_at,
                updated_at=d.updated_at,
            )
            for d in definitions
        ]
