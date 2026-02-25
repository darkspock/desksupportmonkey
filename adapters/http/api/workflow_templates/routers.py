import ulid
from fastapi import APIRouter, Depends, HTTPException, Query

from adapters.http.api.auth.dependencies import require_role
from adapters.http.api.workflow_templates.dependencies import get_workflow_template_repo
from adapters.http.api.workflow_templates.schemas import (
    ChecklistItemDefinitionResponse,
    CreateWorkflowTemplateRequest,
    SubtypeResponse,
    UpdateWorkflowTemplateRequest,
    WorkflowTemplateResponse,
)
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
from src.workflow_bc.template.application.commands.create_template import (
    ChecklistItemInput,
    CreateWorkflowTemplateCommand,
    CreateWorkflowTemplateCommandHandler,
    SubtypeInput,
)
from src.workflow_bc.template.application.commands.delete_template import (
    DeleteWorkflowTemplateCommand,
    DeleteWorkflowTemplateCommandHandler,
)
from src.workflow_bc.template.application.commands.update_template import (
    UpdateWorkflowTemplateCommand,
    UpdateWorkflowTemplateCommandHandler,
)
from src.workflow_bc.template.application.queries.get_template import (
    GetWorkflowTemplateQuery,
    GetWorkflowTemplateQueryHandler,
)
from src.workflow_bc.template.application.queries.list_templates import (
    ListWorkflowTemplatesQuery,
    ListWorkflowTemplatesQueryHandler,
)
from src.workflow_bc.template.domain.exceptions import (
    DuplicateTemplateNameError,
    TemplateHasRequestsError,
    WorkflowTemplateNotFoundError,
)
from src.workflow_bc.template.infrastructure.repository import WorkflowTemplateRepository

router = APIRouter(prefix="/api/v1/workflow-templates", tags=["workflow-templates"])


def _to_response(dto) -> dict:
    return WorkflowTemplateResponse(
        id=dto.id,
        name=dto.name,
        description=dto.description,
        icon=dto.icon,
        is_active=dto.is_active,
        require_all_complete=dto.require_all_complete,
        sort_order=dto.sort_order,
        subtypes=[
            SubtypeResponse(
                id=s.id,
                name=s.name,
                description=s.description,
                sort_order=s.sort_order,
            )
            for s in dto.subtypes
        ],
        checklist_items=[
            ChecklistItemDefinitionResponse(
                id=ci.id,
                title=ci.title,
                description=ci.description,
                assignee_role=ci.assignee_role,
                sort_order=ci.sort_order,
                is_required=ci.is_required,
            )
            for ci in dto.checklist_items
        ],
        created_at=dto.created_at,
        updated_at=dto.updated_at,
    ).model_dump(mode="json")


@router.get("")
def list_templates(
    active: bool = Query(default=False),
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    repo: WorkflowTemplateRepository = Depends(get_workflow_template_repo),
):
    handler = ListWorkflowTemplatesQueryHandler(repo=repo)
    templates = handler.handle(
        ListWorkflowTemplatesQuery(
            company_id=current_user.company_id,
            active_only=active,
        )
    )
    return {"data": [_to_response(t) for t in templates]}


@router.get("/{template_id}")
def get_template(
    template_id: str,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    repo: WorkflowTemplateRepository = Depends(get_workflow_template_repo),
):
    handler = GetWorkflowTemplateQueryHandler(repo=repo)
    try:
        dto = handler.handle(
            GetWorkflowTemplateQuery(
                template_id=template_id,
                company_id=current_user.company_id,
            )
        )
    except WorkflowTemplateNotFoundError:
        raise HTTPException(status_code=404, detail="Workflow template not found")
    return {"data": _to_response(dto)}


@router.post("", status_code=201)
def create_template(
    body: CreateWorkflowTemplateRequest,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    repo: WorkflowTemplateRepository = Depends(get_workflow_template_repo),
):
    template_id = str(ulid.new())
    handler = CreateWorkflowTemplateCommandHandler(repo=repo)
    try:
        handler.handle(
            CreateWorkflowTemplateCommand(
                template_id=template_id,
                company_id=current_user.company_id,
                name=body.name,
                description=body.description,
                icon=body.icon,
                require_all_complete=body.require_all_complete,
                sort_order=body.sort_order,
                subtypes=[
                    SubtypeInput(
                        name=s.name,
                        description=s.description,
                        sort_order=s.sort_order,
                    )
                    for s in body.subtypes
                ],
                checklist_items=[
                    ChecklistItemInput(
                        title=ci.title,
                        description=ci.description,
                        assignee_role=ci.assignee_role,
                        sort_order=ci.sort_order,
                        is_required=ci.is_required,
                    )
                    for ci in body.checklist_items
                ],
            )
        )
    except DuplicateTemplateNameError as e:
        raise HTTPException(status_code=409, detail=str(e))

    query_handler = GetWorkflowTemplateQueryHandler(repo=repo)
    dto = query_handler.handle(
        GetWorkflowTemplateQuery(
            template_id=template_id,
            company_id=current_user.company_id,
        )
    )
    return {"data": _to_response(dto)}


@router.put("/{template_id}")
def update_template(
    template_id: str,
    body: UpdateWorkflowTemplateRequest,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    repo: WorkflowTemplateRepository = Depends(get_workflow_template_repo),
):
    handler = UpdateWorkflowTemplateCommandHandler(repo=repo)
    try:
        handler.handle(
            UpdateWorkflowTemplateCommand(
                template_id=template_id,
                company_id=current_user.company_id,
                name=body.name,
                description=body.description,
                icon=body.icon,
                is_active=body.is_active,
                require_all_complete=body.require_all_complete,
                sort_order=body.sort_order,
                subtypes=[
                    SubtypeInput(
                        name=s.name,
                        description=s.description,
                        sort_order=s.sort_order,
                    )
                    for s in body.subtypes
                ]
                if body.subtypes is not None
                else None,
                checklist_items=[
                    ChecklistItemInput(
                        title=ci.title,
                        description=ci.description,
                        assignee_role=ci.assignee_role,
                        sort_order=ci.sort_order,
                        is_required=ci.is_required,
                    )
                    for ci in body.checklist_items
                ]
                if body.checklist_items is not None
                else None,
            )
        )
    except WorkflowTemplateNotFoundError:
        raise HTTPException(status_code=404, detail="Workflow template not found")
    except DuplicateTemplateNameError as e:
        raise HTTPException(status_code=409, detail=str(e))

    query_handler = GetWorkflowTemplateQueryHandler(repo=repo)
    dto = query_handler.handle(
        GetWorkflowTemplateQuery(
            template_id=template_id,
            company_id=current_user.company_id,
        )
    )
    return {"data": _to_response(dto)}


@router.delete("/{template_id}", status_code=204)
def delete_template(
    template_id: str,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    repo: WorkflowTemplateRepository = Depends(get_workflow_template_repo),
):
    handler = DeleteWorkflowTemplateCommandHandler(repo=repo)
    try:
        handler.handle(
            DeleteWorkflowTemplateCommand(
                template_id=template_id,
                company_id=current_user.company_id,
            )
        )
    except WorkflowTemplateNotFoundError:
        raise HTTPException(status_code=404, detail="Workflow template not found")
    except TemplateHasRequestsError as e:
        raise HTTPException(status_code=409, detail=str(e))
