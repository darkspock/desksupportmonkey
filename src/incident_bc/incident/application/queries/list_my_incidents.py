from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from src.framework.application.query_bus import Query, QueryHandler
from src.incident_bc.incident.domain.repository import IncidentRepositoryInterface


@dataclass
class MyIncidentDto:
    """Restricted DTO for employee view -- no sensitive fields."""

    id: str
    title: str
    incident_type: str
    severity: str
    status: str
    created_at: Optional[datetime]


@dataclass
class ListMyIncidentsQuery(Query):
    user_id: str
    company_id: str


class ListMyIncidentsQueryHandler(
    QueryHandler[ListMyIncidentsQuery, list[MyIncidentDto]]
):
    def __init__(self, incident_repo: IncidentRepositoryInterface):
        self.incident_repo = incident_repo

    def handle(self, query: ListMyIncidentsQuery) -> list[MyIncidentDto]:
        incidents = self.incident_repo.find_my_incidents(
            query.user_id, query.company_id
        )
        return [
            MyIncidentDto(
                id=i.id,
                title=i.title,
                incident_type=i.incident_type.value,
                severity=i.severity.value,
                status=i.status.value,
                created_at=i.created_at,
            )
            for i in incidents
        ]
