from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Optional

from src.framework.application.query_bus import Query, QueryHandler
from src.incident_bc.incident.domain.repository import (
    IncidentFilters,
    IncidentRepositoryInterface,
)


@dataclass
class IncidentListDto:
    id: str
    title: str
    incident_type: str
    severity: str
    status: str
    assigned_to: Optional[str]
    assigned_to_name: Optional[str]
    detected_at: Optional[datetime]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    custom_fields_data: Optional[dict] = None


@dataclass
class ListIncidentsQuery(Query):
    company_id: str
    page: int = 1
    page_size: int = 20
    status: Optional[str] = None
    severity: Optional[str] = None
    incident_type: Optional[str] = None
    search: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    custom_field_filters: Optional[dict[str, str]] = None
    custom_field_search_keys: Optional[list[str]] = None


class ListIncidentsQueryHandler(
    QueryHandler[ListIncidentsQuery, tuple[list[IncidentListDto], int]]
):
    def __init__(
        self,
        incident_repo: IncidentRepositoryInterface,
        user_name_resolver: Optional[Callable[[list[str]], dict[str, str]]] = None,
    ):
        self.incident_repo = incident_repo
        self.user_name_resolver = user_name_resolver

    def handle(
        self, query: ListIncidentsQuery
    ) -> tuple[list[IncidentListDto], int]:
        filters = IncidentFilters(
            page=query.page,
            page_size=query.page_size,
            status=query.status,
            severity=query.severity,
            incident_type=query.incident_type,
            search=query.search,
            date_from=query.date_from,
            date_to=query.date_to,
            custom_field_filters=query.custom_field_filters,
            custom_field_search_keys=query.custom_field_search_keys,
        )
        incidents, total = self.incident_repo.find_all(
            query.company_id, filters
        )

        # Resolve user names in batch
        name_map: dict[str, str] = {}
        if self.user_name_resolver:
            user_ids = {
                i.assigned_to for i in incidents if i.assigned_to
            }
            if user_ids:
                name_map = self.user_name_resolver(list(user_ids))

        items = [
            IncidentListDto(
                id=i.id,
                title=i.title,
                incident_type=i.incident_type.value,
                severity=i.severity.value,
                status=i.status.value,
                assigned_to=i.assigned_to,
                assigned_to_name=name_map.get(i.assigned_to) if i.assigned_to else None,
                detected_at=i.detected_at,
                created_at=i.created_at,
                updated_at=i.updated_at,
                custom_fields_data=i.custom_fields_data,
            )
            for i in incidents
        ]
        return items, total
