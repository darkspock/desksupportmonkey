from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from src.framework.application.query_bus import Query, QueryHandler
from src.workflow_bc.checklist.domain.repository import ChecklistItemRepositoryInterface


@dataclass
class ChecklistItemDto:
    id: str
    request_id: str
    title: str
    description: Optional[str]
    assignee_id: Optional[str]
    is_required: bool
    is_completed: bool
    completed_by: Optional[str]
    completed_at: Optional[datetime]
    sort_order: int
    created_at: Optional[datetime]


@dataclass
class ListChecklistItemsQuery(Query):
    request_id: str


class ListChecklistItemsQueryHandler(
    QueryHandler[ListChecklistItemsQuery, list[ChecklistItemDto]]
):
    def __init__(self, repo: ChecklistItemRepositoryInterface):
        self.repo = repo

    def handle(self, query: ListChecklistItemsQuery) -> list[ChecklistItemDto]:
        items = self.repo.find_by_request(query.request_id)
        return [
            ChecklistItemDto(
                id=i.id,
                request_id=i.request_id,
                title=i.title,
                description=i.description,
                assignee_id=i.assignee_id,
                is_required=i.is_required,
                is_completed=i.is_completed,
                completed_by=i.completed_by,
                completed_at=i.completed_at,
                sort_order=i.sort_order,
                created_at=i.created_at,
            )
            for i in items
        ]
