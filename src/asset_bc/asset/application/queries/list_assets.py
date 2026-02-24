from dataclasses import dataclass
from typing import Optional

from src.asset_bc.asset.domain.entities import Asset
from src.asset_bc.asset.domain.repository import AssetRepositoryInterface
from src.framework.application.query_bus import Query, QueryHandler


@dataclass
class ListAssetsQuery(Query):
    company_id: str
    page: int = 1
    page_size: int = 20
    search: Optional[str] = None
    type: Optional[str] = None
    status: Optional[str] = None
    department_id: Optional[str] = None
    assigned_to: Optional[str] = None
    location_id: Optional[str] = None
    sort_by: str = "created_at"
    sort_order: str = "desc"
    custom_field_filters: Optional[dict[str, str]] = None
    custom_field_search_keys: Optional[list[str]] = None


class ListAssetsQueryHandler(QueryHandler[ListAssetsQuery, tuple[list[Asset], int]]):
    def __init__(self, asset_repo: AssetRepositoryInterface):
        self.asset_repo = asset_repo

    def handle(self, query: ListAssetsQuery) -> tuple[list[Asset], int]:
        return self.asset_repo.find_all(
            company_id=query.company_id,
            page=query.page,
            page_size=query.page_size,
            search=query.search,
            type=query.type,
            status=query.status,
            department_id=query.department_id,
            assigned_to=query.assigned_to,
            location_id=query.location_id,
            sort_by=query.sort_by,
            sort_order=query.sort_order,
            custom_field_filters=query.custom_field_filters,
            custom_field_search_keys=query.custom_field_search_keys,
        )
