from fastapi import APIRouter, Depends, HTTPException

from adapters.http.api.auth.dependencies import require_role
from adapters.http.api.checklist.dependencies import (
    get_checklist_repo,
    get_template_repo_for_checklist,
)
from adapters.http.api.checklist.schemas import (
    AddChecklistItemRequest,
    AssignChecklistItemRequest,
    ChecklistItemResponse,
    ChecklistProgressResponse,
)
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
from src.workflow_bc.checklist.application.commands.add_item import (
    AddChecklistItemCommand,
    AddChecklistItemCommandHandler,
)
from src.workflow_bc.checklist.application.commands.assign_item import (
    AssignChecklistItemCommand,
    AssignChecklistItemCommandHandler,
)
from src.workflow_bc.checklist.application.commands.remove_item import (
    RemoveChecklistItemCommand,
    RemoveChecklistItemCommandHandler,
)
from src.workflow_bc.checklist.application.commands.toggle_item import (
    ToggleChecklistItemCommand,
    ToggleChecklistItemCommandHandler,
)
from src.workflow_bc.checklist.application.queries.list_items import (
    ListChecklistItemsQuery,
    ListChecklistItemsQueryHandler,
)
from src.workflow_bc.checklist.domain.exceptions import ChecklistItemNotFoundError
from src.workflow_bc.checklist.infrastructure.repository import ChecklistItemRepository

router = APIRouter(
    prefix="/api/v1/requests/{request_id}/checklist",
    tags=["checklist"],
)


def _to_response(dto) -> dict:
    return ChecklistItemResponse(
        id=dto.id,
        request_id=dto.request_id,
        title=dto.title,
        description=dto.description,
        assignee_id=dto.assignee_id,
        is_required=dto.is_required,
        is_completed=dto.is_completed,
        completed_by=dto.completed_by,
        completed_at=dto.completed_at,
        sort_order=dto.sort_order,
        created_at=dto.created_at,
    ).model_dump(mode="json")


def _progress(items: list) -> dict:
    total = len(items)
    completed = sum(1 for i in items if i.is_completed)
    required_remaining = sum(
        1 for i in items if i.is_required and not i.is_completed
    )
    return ChecklistProgressResponse(
        total=total,
        completed=completed,
        required_remaining=required_remaining,
    ).model_dump()


@router.get("")
def list_checklist(
    request_id: str,
    current_user: User = Depends(require_role(UserRole.EMPLOYEE)),
    repo: ChecklistItemRepository = Depends(get_checklist_repo),
):
    handler = ListChecklistItemsQueryHandler(repo=repo)
    items = handler.handle(ListChecklistItemsQuery(request_id=request_id))
    return {
        "data": [_to_response(i) for i in items],
        "progress": _progress(items),
    }


@router.post("", status_code=201)
def add_checklist_item(
    request_id: str,
    body: AddChecklistItemRequest,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    repo: ChecklistItemRepository = Depends(get_checklist_repo),
):
    handler = AddChecklistItemCommandHandler(repo=repo)
    handler.handle(
        AddChecklistItemCommand(
            request_id=request_id,
            title=body.title,
            description=body.description,
            assignee_id=body.assignee_id,
            is_required=body.is_required,
        )
    )
    # Return updated list
    query_handler = ListChecklistItemsQueryHandler(repo=repo)
    items = query_handler.handle(ListChecklistItemsQuery(request_id=request_id))
    return {
        "data": [_to_response(i) for i in items],
        "progress": _progress(items),
    }


@router.patch("/{item_id}/toggle")
def toggle_checklist_item(
    request_id: str,
    item_id: str,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    repo: ChecklistItemRepository = Depends(get_checklist_repo),
):
    handler = ToggleChecklistItemCommandHandler(repo=repo)
    try:
        handler.handle(
            ToggleChecklistItemCommand(
                item_id=item_id,
                user_id=current_user.id,
            )
        )
    except ChecklistItemNotFoundError:
        raise HTTPException(status_code=404, detail="Checklist item not found")

    query_handler = ListChecklistItemsQueryHandler(repo=repo)
    items = query_handler.handle(ListChecklistItemsQuery(request_id=request_id))
    return {
        "data": [_to_response(i) for i in items],
        "progress": _progress(items),
    }


@router.patch("/{item_id}/assign")
def assign_checklist_item(
    request_id: str,
    item_id: str,
    body: AssignChecklistItemRequest,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    repo: ChecklistItemRepository = Depends(get_checklist_repo),
):
    handler = AssignChecklistItemCommandHandler(repo=repo)
    try:
        handler.handle(
            AssignChecklistItemCommand(
                item_id=item_id,
                assignee_id=body.assignee_id,
            )
        )
    except ChecklistItemNotFoundError:
        raise HTTPException(status_code=404, detail="Checklist item not found")

    query_handler = ListChecklistItemsQueryHandler(repo=repo)
    items = query_handler.handle(ListChecklistItemsQuery(request_id=request_id))
    return {
        "data": [_to_response(i) for i in items],
        "progress": _progress(items),
    }


@router.delete("/{item_id}", status_code=204)
def remove_checklist_item(
    request_id: str,
    item_id: str,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    repo: ChecklistItemRepository = Depends(get_checklist_repo),
):
    handler = RemoveChecklistItemCommandHandler(repo=repo)
    try:
        handler.handle(RemoveChecklistItemCommand(item_id=item_id))
    except ChecklistItemNotFoundError:
        raise HTTPException(status_code=404, detail="Checklist item not found")
