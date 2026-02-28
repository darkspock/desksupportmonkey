from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Optional

from src.framework.application.query_bus import Query, QueryHandler
from src.change_bc.change_request.domain.repository import (
    ChangeRequestFilters,
    ChangeRequestRepositoryInterface,
)


@dataclass
class ChangeRequestListDto:
    id: str
    title: str
    change_type: str
    status: str
    planned_date: Optional[datetime]
    assigned_to: Optional[str]
    assigned_to_name: Optional[str]
    requested_by: str
    requested_by_name: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


@dataclass
class ListChangeRequestsQuery(Query):
    company_id: str
    page: int = 1
    page_size: int = 20
    status: Optional[str] = None
    change_type: Optional[str] = None
    assigned_to: Optional[str] = None
    search: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


class ListChangeRequestsQueryHandler(
    QueryHandler[
        ListChangeRequestsQuery,
        tuple[list[ChangeRequestListDto], int],
    ]
):
    def __init__(
        self,
        change_repo: ChangeRequestRepositoryInterface,
        user_name_resolver: Optional[Callable] = None,
    ):
        self.change_repo = change_repo
        self.user_name_resolver = user_name_resolver

    def handle(
        self, query: ListChangeRequestsQuery
    ) -> tuple[list[ChangeRequestListDto], int]:
        changes, total = self.change_repo.find_all(
            company_id=query.company_id,
            filters=ChangeRequestFilters(
                page=query.page,
                page_size=query.page_size,
                status=query.status,
                change_type=query.change_type,
                assigned_to=query.assigned_to,
                search=query.search,
                date_from=query.date_from,
                date_to=query.date_to,
            ),
        )

        name_map: dict[str, str] = {}
        if self.user_name_resolver:
            user_ids: set[str] = set()
            for c in changes:
                if c.assigned_to:
                    user_ids.add(c.assigned_to)
                if c.requested_by:
                    user_ids.add(c.requested_by)
            if user_ids:
                name_map = self.user_name_resolver(list(user_ids))

        return [
            ChangeRequestListDto(
                id=c.id,
                title=c.title,
                change_type=c.change_type.value,
                status=c.status.value,
                planned_date=c.planned_date,
                assigned_to=c.assigned_to,
                assigned_to_name=(
                    name_map.get(c.assigned_to)
                    if c.assigned_to
                    else None
                ),
                requested_by=c.requested_by,
                requested_by_name=name_map.get(c.requested_by),
                created_at=c.created_at,
                updated_at=c.updated_at,
            )
            for c in changes
        ], total
