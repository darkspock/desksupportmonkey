from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from src.framework.application.query_bus import Query, QueryHandler
from src.workflow_bc.template.domain.repository import WorkflowTemplateRepositoryInterface


@dataclass
class SubtypeDto:
    id: str
    name: str
    description: Optional[str]
    sort_order: int


@dataclass
class ChecklistItemDefinitionDto:
    id: str
    title: str
    description: Optional[str]
    assignee_role: Optional[str]
    sort_order: int
    is_required: bool


@dataclass
class WorkflowTemplateDto:
    id: str
    company_id: str
    name: str
    description: Optional[str]
    icon: Optional[str]
    is_active: bool
    require_all_complete: bool
    sort_order: int
    subtypes: list[SubtypeDto] = field(default_factory=list)
    checklist_items: list[ChecklistItemDefinitionDto] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class ListWorkflowTemplatesQuery(Query):
    company_id: str
    active_only: bool = False


class ListWorkflowTemplatesQueryHandler(
    QueryHandler[ListWorkflowTemplatesQuery, list[WorkflowTemplateDto]]
):
    def __init__(self, repo: WorkflowTemplateRepositoryInterface):
        self.repo = repo

    def handle(
        self, query: ListWorkflowTemplatesQuery
    ) -> list[WorkflowTemplateDto]:
        templates = self.repo.find_by_company(
            company_id=query.company_id,
            active_only=query.active_only,
        )
        return [
            WorkflowTemplateDto(
                id=t.id,
                company_id=t.company_id,
                name=t.name,
                description=t.description,
                icon=t.icon,
                is_active=t.is_active,
                require_all_complete=t.require_all_complete,
                sort_order=t.sort_order,
                subtypes=[
                    SubtypeDto(
                        id=s.id,
                        name=s.name,
                        description=s.description,
                        sort_order=s.sort_order,
                    )
                    for s in t.subtypes
                ],
                checklist_items=[
                    ChecklistItemDefinitionDto(
                        id=ci.id,
                        title=ci.title,
                        description=ci.description,
                        assignee_role=ci.assignee_role,
                        sort_order=ci.sort_order,
                        is_required=ci.is_required,
                    )
                    for ci in t.checklist_items
                ],
                created_at=t.created_at,
                updated_at=t.updated_at,
            )
            for t in templates
        ]
