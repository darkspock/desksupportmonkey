from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Optional

from src.framework.application.query_bus import Query, QueryHandler
from src.incident_bc.incident.domain.exceptions import (
    IncidentNotFoundError,
    PostMortemNotFoundError,
)
from src.incident_bc.incident.domain.repository import IncidentRepositoryInterface


@dataclass
class PostMortemDto:
    id: str
    root_cause: str
    lessons_learned: str
    corrective_actions: str
    created_by: str
    created_by_name: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


@dataclass
class GetPostMortemQuery(Query):
    incident_id: str
    company_id: str


class GetPostMortemQueryHandler(
    QueryHandler[GetPostMortemQuery, Optional[PostMortemDto]]
):
    def __init__(
        self,
        incident_repo: IncidentRepositoryInterface,
        user_name_resolver: Optional[Callable[[list[str]], dict[str, str]]] = None,
    ):
        self.incident_repo = incident_repo
        self.user_name_resolver = user_name_resolver

    def handle(self, query: GetPostMortemQuery) -> Optional[PostMortemDto]:
        incident = self.incident_repo.find_by_id(
            query.incident_id, query.company_id
        )
        if not incident:
            raise IncidentNotFoundError(query.incident_id)

        pm = self.incident_repo.find_postmortem_by_incident(query.incident_id)
        if not pm:
            return None

        created_by_name = None
        if self.user_name_resolver and pm.get("created_by"):
            name_map = self.user_name_resolver([pm["created_by"]])
            created_by_name = name_map.get(pm["created_by"])

        return PostMortemDto(
            id=pm["id"],
            root_cause=pm["root_cause"],
            lessons_learned=pm["lessons_learned"],
            corrective_actions=pm["corrective_actions"],
            created_by=pm["created_by"],
            created_by_name=created_by_name,
            created_at=pm.get("created_at"),
            updated_at=pm.get("updated_at"),
        )
