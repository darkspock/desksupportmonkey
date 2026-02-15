import logging

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from adapters.http.api.auth.dependencies import get_current_user, require_role
from adapters.http.api.requests.schemas import (
    AddCommentRequest,
    AssignRequestRequest,
    ChangePriorityRequest,
    ChangeStatusRequest,
    CommentResponse,
    CreateRequestRequest,
    NoteResponse,
    RequestListItemResponse,
    RequestResponse,
)
from adapters.http.schemas.responses import PaginationMeta
from core.database import get_db
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
from src.request_bc.request.application.commands.create_request import (
    CreateRequestCommand,
    CreateRequestCommandHandler,
)
from src.request_bc.request.application.commands.change_request_status import (
    ChangeRequestStatusCommand,
    ChangeRequestStatusCommandHandler,
    RequestNotFoundError as StatusRequestNotFoundError,
)
from src.request_bc.request.application.commands.change_request_priority import (
    ChangeRequestPriorityCommand,
    ChangeRequestPriorityCommandHandler,
    RequestNotFoundError as PriorityRequestNotFoundError,
)
from src.request_bc.request.application.commands.assign_request import (
    AssignRequestCommand,
    AssignRequestCommandHandler,
    RequestNotFoundError as AssignRequestNotFoundError,
    UserNotFoundError,
    UserInactiveError,
)
from src.request_bc.request.application.queries.get_request import (
    GetRequestQuery,
    GetRequestQueryHandler,
    RequestNotFoundError as GetRequestNotFoundError,
)
from src.request_bc.request.application.commands.add_comment import (
    AddCommentCommand,
    AddCommentCommandHandler,
    RequestNotFoundError as CommentRequestNotFoundError,
)
from src.request_bc.request.application.commands.add_note import (
    AddNoteCommand,
    AddNoteCommandHandler,
    RequestNotFoundError as NoteRequestNotFoundError,
)
from src.request_bc.request.application.queries.list_requests import (
    ListRequestsQuery,
    ListRequestsQueryHandler,
)
from src.request_bc.request.application.queries.list_comments import (
    ListCommentsQuery,
    ListCommentsQueryHandler,
    RequestNotFoundError as ListCommentsRequestNotFoundError,
)
from src.request_bc.request.application.queries.list_notes import (
    ListNotesQuery,
    ListNotesQueryHandler,
    RequestNotFoundError as ListNotesRequestNotFoundError,
)
from src.request_bc.request.domain.entities import ServiceRequest
from src.request_bc.request.domain.enums import InvalidStatusTransitionError
from src.request_bc.request.infrastructure.repository import RequestRepository
from src.auth_bc.user.infrastructure.repository import UserRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/requests", tags=["requests"])


def _to_response(request: ServiceRequest, comment_count: int = 0) -> RequestResponse:
    return RequestResponse(
        id=request.id,
        company_id=request.company_id,
        created_by=request.created_by,
        assigned_to=request.assigned_to,
        type=request.type.value,
        title=request.title,
        description=request.description,
        status=request.status.value,
        priority=request.priority.value,
        data=request.data,
        resolved_at=request.resolved_at,
        created_at=request.created_at,
        updated_at=request.updated_at,
        comment_count=comment_count,
    )


@router.get("")
def list_requests(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    request_status: Optional[str] = Query(None, alias="status"),
    type: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    assigned_to: Optional[str] = Query(None),
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    db: Session = Depends(get_db),
):
    # Translate "me" shorthand to current user's ID
    effective_assigned_to = assigned_to
    if assigned_to == "me":
        effective_assigned_to = current_user.id

    handler = ListRequestsQueryHandler(request_repo=RequestRepository(db))
    requests, total = handler.handle(
        ListRequestsQuery(
            company_id=current_user.company_id,
            page=page,
            page_size=page_size,
            search=search,
            status=request_status,
            type=type,
            priority=priority,
            assigned_to=effective_assigned_to,
        )
    )
    return {
        "data": [
            RequestListItemResponse(
                id=r.id,
                type=r.type.value,
                title=r.title,
                status=r.status.value,
                priority=r.priority.value,
                assigned_to=r.assigned_to,
                created_by=r.created_by,
                created_at=r.created_at,
                updated_at=r.updated_at,
            ).model_dump(mode="json")
            for r in requests
        ],
        "meta": PaginationMeta(page=page, page_size=page_size, total=total).model_dump(),
    }


@router.post("", status_code=status.HTTP_201_CREATED)
def create_request(
    body: CreateRequestRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    handler = CreateRequestCommandHandler(request_repo=RequestRepository(db))
    try:
        request = handler.handle(
            CreateRequestCommand(
                company_id=current_user.company_id,
                created_by=current_user.id,
                type=body.type,
                title=body.title,
                description=body.description,
                data=body.data,
            )
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    return {"data": _to_response(request).model_dump(mode="json")}


@router.get("/{request_id}")
def get_request(
    request_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    handler = GetRequestQueryHandler(request_repo=RequestRepository(db))
    try:
        detail = handler.handle(
            GetRequestQuery(request_id=request_id, company_id=current_user.company_id)
        )
    except GetRequestNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

    # Employee access control: can only see own requests
    if not current_user.role.has_access(UserRole.TECHNICIAN):
        if detail.request.created_by != current_user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

    return {"data": _to_response(detail.request, detail.comment_count).model_dump(mode="json")}


@router.patch("/{request_id}/status")
def change_request_status(
    request_id: str,
    body: ChangeStatusRequest,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    db: Session = Depends(get_db),
):
    handler = ChangeRequestStatusCommandHandler(request_repo=RequestRepository(db))
    try:
        request = handler.handle(
            ChangeRequestStatusCommand(
                request_id=request_id,
                company_id=current_user.company_id,
                new_status=body.status,
                performed_by=current_user.id,
            )
        )
    except StatusRequestNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    except InvalidStatusTransitionError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    return {"data": _to_response(request).model_dump(mode="json")}


@router.patch("/{request_id}/priority")
def change_request_priority(
    request_id: str,
    body: ChangePriorityRequest,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    db: Session = Depends(get_db),
):
    handler = ChangeRequestPriorityCommandHandler(request_repo=RequestRepository(db))
    try:
        request = handler.handle(
            ChangeRequestPriorityCommand(
                request_id=request_id,
                company_id=current_user.company_id,
                new_priority=body.priority,
                performed_by=current_user.id,
            )
        )
    except PriorityRequestNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    return {"data": _to_response(request).model_dump(mode="json")}


@router.patch("/{request_id}/assign")
def assign_request(
    request_id: str,
    body: AssignRequestRequest,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    db: Session = Depends(get_db),
):
    handler = AssignRequestCommandHandler(
        request_repo=RequestRepository(db),
        user_repo=UserRepository(db),
    )
    try:
        request = handler.handle(
            AssignRequestCommand(
                request_id=request_id,
                company_id=current_user.company_id,
                user_id=body.user_id,
                performed_by=current_user.id,
            )
        )
    except AssignRequestNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    except UserNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    except UserInactiveError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User is inactive")
    return {"data": _to_response(request).model_dump(mode="json")}


def _verify_request_access(request_id: str, company_id: str, current_user: User, db: Session):
    """Verify employee can access the request (owns it) or technician+ can access any."""
    repo = RequestRepository(db)
    request = repo.find_by_id(request_id, company_id)
    if not request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    if not current_user.role.has_access(UserRole.TECHNICIAN):
        if request.created_by != current_user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    return request


@router.post("/{request_id}/comments", status_code=status.HTTP_201_CREATED)
def add_comment(
    request_id: str,
    body: AddCommentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _verify_request_access(request_id, current_user.company_id, current_user, db)
    handler = AddCommentCommandHandler(request_repo=RequestRepository(db))
    try:
        comment = handler.handle(
            AddCommentCommand(
                request_id=request_id,
                company_id=current_user.company_id,
                author_id=current_user.id,
                body=body.body,
            )
        )
    except CommentRequestNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    return {
        "data": CommentResponse(
            id=comment.id,
            request_id=comment.request_id,
            author_id=comment.author_id,
            body=comment.body,
            created_at=comment.created_at,
        ).model_dump(mode="json")
    }


@router.get("/{request_id}/comments")
def list_comments(
    request_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _verify_request_access(request_id, current_user.company_id, current_user, db)
    handler = ListCommentsQueryHandler(request_repo=RequestRepository(db))
    try:
        comments = handler.handle(
            ListCommentsQuery(request_id=request_id, company_id=current_user.company_id)
        )
    except ListCommentsRequestNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    return {
        "data": [
            CommentResponse(
                id=c.id,
                request_id=c.request_id,
                author_id=c.author_id,
                body=c.body,
                created_at=c.created_at,
            ).model_dump(mode="json")
            for c in comments
        ]
    }


@router.post("/{request_id}/notes", status_code=status.HTTP_201_CREATED)
def add_note(
    request_id: str,
    body: AddCommentRequest,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    db: Session = Depends(get_db),
):
    handler = AddNoteCommandHandler(request_repo=RequestRepository(db))
    try:
        note = handler.handle(
            AddNoteCommand(
                request_id=request_id,
                company_id=current_user.company_id,
                author_id=current_user.id,
                body=body.body,
            )
        )
    except NoteRequestNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    return {
        "data": NoteResponse(
            id=note.id,
            request_id=note.request_id,
            author_id=note.author_id,
            body=note.body,
            created_at=note.created_at,
        ).model_dump(mode="json")
    }


@router.get("/{request_id}/notes")
def list_notes(
    request_id: str,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    db: Session = Depends(get_db),
):
    handler = ListNotesQueryHandler(request_repo=RequestRepository(db))
    try:
        notes = handler.handle(
            ListNotesQuery(request_id=request_id, company_id=current_user.company_id)
        )
    except ListNotesRequestNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    return {
        "data": [
            NoteResponse(
                id=n.id,
                request_id=n.request_id,
                author_id=n.author_id,
                body=n.body,
                created_at=n.created_at,
            ).model_dump(mode="json")
            for n in notes
        ]
    }
