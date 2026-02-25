from dataclasses import dataclass

from src.framework.application.query_bus import Query, QueryHandler
from src.workflow_bc.template.domain.exceptions import WorkflowTemplateNotFoundError
from src.workflow_bc.template.domain.repository import WorkflowTemplateRepositoryInterface
from src.workflow_bc.template.application.queries.list_templates import (
    ChecklistItemDefinitionDto,
    SubtypeDto,
    WorkflowTemplateDto,
)


@dataclass
class GetWorkflowTemplateQuery(Query):
    template_id: str
    company_id: str


class GetWorkflowTemplateQueryHandler(
    QueryHandler[GetWorkflowTemplateQuery, WorkflowTemplateDto]
):
    def __init__(self, repo: WorkflowTemplateRepositoryInterface):
        self.repo = repo

    def handle(self, query: GetWorkflowTemplateQuery) -> WorkflowTemplateDto:
        template = self.repo.find_by_id(query.template_id, query.company_id)
        if not template:
            raise WorkflowTemplateNotFoundError(query.template_id)

        return WorkflowTemplateDto(
            id=template.id,
            company_id=template.company_id,
            name=template.name,
            description=template.description,
            icon=template.icon,
            is_active=template.is_active,
            require_all_complete=template.require_all_complete,
            sort_order=template.sort_order,
            subtypes=[
                SubtypeDto(
                    id=s.id,
                    name=s.name,
                    description=s.description,
                    sort_order=s.sort_order,
                )
                for s in template.subtypes
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
                for ci in template.checklist_items
            ],
            created_at=template.created_at,
            updated_at=template.updated_at,
        )
