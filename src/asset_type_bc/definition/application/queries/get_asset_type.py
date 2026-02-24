from dataclasses import dataclass

from src.framework.application.query_bus import Query, QueryHandler
from src.asset_type_bc.definition.domain.exceptions import (
    AssetTypeDefinitionNotFoundError,
)
from src.asset_type_bc.definition.domain.repository import (
    AssetTypeDefinitionRepositoryInterface,
)
from src.asset_type_bc.definition.application.queries.list_asset_types import (
    AssetTypeDto,
)


@dataclass
class GetAssetTypeQuery(Query):
    definition_id: str
    company_id: str


class GetAssetTypeQueryHandler(
    QueryHandler[GetAssetTypeQuery, AssetTypeDto]
):
    def __init__(
        self, repo: AssetTypeDefinitionRepositoryInterface
    ):
        self.repo = repo

    def handle(self, query: GetAssetTypeQuery) -> AssetTypeDto:
        d = self.repo.find_by_id(
            query.definition_id, query.company_id
        )
        if not d:
            raise AssetTypeDefinitionNotFoundError(
                query.definition_id
            )
        return AssetTypeDto(
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
