import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from adapters.http.api.auth.dependencies import require_role
from adapters.http.api.support.schemas import (
    AddMessageRequest,
    ChangePriorityRequest,
    ChangeStatusRequest,
    TicketDetailResponse,
    TicketListItemResponse,
    TicketMessageResponse,
    TicketStatsResponse,
)
from adapters.http.schemas.responses import PaginationMeta
from core.database import get_db
from core.tasks.support_ticket_emails import send_support_ticket_email
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
from src.auth_bc.user.infrastructure.repository import UserRepository
from src.support_bc.ticket.application.commands.add_message import (
    AddTicketMessageCommand,
    AddTicketMessageCommandHandler,
)
from src.support_bc.ticket.application.commands.change_priority import (
    ChangeTicketPriorityCommand,
    ChangeTicketPriorityCommandHandler,
)
from src.support_bc.ticket.application.commands.change_status import (
    ChangeTicketStatusCommand,
    ChangeTicketStatusCommandHandler,
)
from src.support_bc.ticket.application.queries.get_ticket_detail import (
    GetTicketDetailQuery,
    GetTicketDetailQueryHandler,
    TicketDetail,
)
from src.support_bc.ticket.application.queries.get_ticket_stats import (
    GetTicketStatsQuery,
    GetTicketStatsQueryHandler,
)
from src.support_bc.ticket.application.queries.list_all_tickets import (
    ListAllTicketsQuery,
    ListAllTicketsQueryHandler,
)
from src.support_bc.ticket.domain.entities import SupportTicket
from src.support_bc.ticket.domain.enums import TicketStatus
from src.support_bc.ticket.domain.exceptions import (
    InvalidTicketTransitionError,
    TicketNotFoundError,
)
from src.support_bc.ticket.infrastructure.repository import SupportTicketRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/support-tickets", tags=["support-tickets"])


def _to_list_item(ticket: SupportTicket, users: dict | None = None) -> dict:
    creator = users.get(ticket.created_by) if users else None
    return TicketListItemResponse(
        id=ticket.id,
        reference=ticket.reference,
        category=ticket.category.value,
        subject=ticket.subject,
        status=ticket.status.value,
        priority=ticket.priority.value,
        company_id=ticket.company_id,
        created_by_email=creator.email if creator else None,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        resolved_at=ticket.resolved_at,
    ).model_dump(mode="json")


def _to_response(ticket: SupportTicket, users: dict | None = None) -> dict:
    creator = users.get(ticket.created_by) if users else None
    return TicketDetailResponse(
        id=ticket.id,
        reference=ticket.reference,
        company_id=ticket.company_id,
        created_by=ticket.created_by,
        created_by_name=creator.name if creator else None,
        created_by_email=creator.email if creator else None,
        category=ticket.category.value,
        subject=ticket.subject,
        description=ticket.description,
        status=ticket.status.value,
        priority=ticket.priority.value,
        ai_conversation_summary=ticket.ai_conversation_summary,
        resolved_at=ticket.resolved_at,
        closed_at=ticket.closed_at,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        satisfaction_rating=ticket.satisfaction_rating,
        satisfaction_comment=ticket.satisfaction_comment,
        rated_at=ticket.rated_at,
    ).model_dump(mode="json")


def _to_detail_response(detail: TicketDetail, users: dict) -> dict:
    creator = users.get(detail.ticket.created_by)
    response = TicketDetailResponse(
        id=detail.ticket.id,
        reference=detail.ticket.reference,
        company_id=detail.ticket.company_id,
        created_by=detail.ticket.created_by,
        created_by_name=creator.name if creator else None,
        created_by_email=creator.email if creator else None,
        category=detail.ticket.category.value,
        subject=detail.ticket.subject,
        description=detail.ticket.description,
        status=detail.ticket.status.value,
        priority=detail.ticket.priority.value,
        ai_conversation_summary=detail.ticket.ai_conversation_summary,
        resolved_at=detail.ticket.resolved_at,
        closed_at=detail.ticket.closed_at,
        created_at=detail.ticket.created_at,
        updated_at=detail.ticket.updated_at,
        satisfaction_rating=detail.ticket.satisfaction_rating,
        satisfaction_comment=detail.ticket.satisfaction_comment,
        rated_at=detail.ticket.rated_at,
        messages=[
            TicketMessageResponse(
                id=m.id,
                author_id=m.author_id,
                author_name=users[m.author_id].name if m.author_id in users else None,
                author_email=users[m.author_id].email if m.author_id in users else None,
                body=m.body,
                is_from_platform=m.is_from_platform,
                created_at=m.created_at,
            )
            for m in detail.messages
        ],
    )
    return response.model_dump(mode="json")


@router.get("")
def list_all_tickets(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    ticket_status: Optional[str] = Query(None, alias="status"),
    category: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    company_id: Optional[str] = Query(None),
    sort_by: Optional[str] = Query(None),
    sort_order: Optional[str] = Query(None),
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db),
):
    ticket_repo = SupportTicketRepository(db)
    user_repo = UserRepository(db)
    handler = ListAllTicketsQueryHandler(ticket_repo=ticket_repo)
    tickets, total = handler.handle(
        ListAllTicketsQuery(
            page=page,
            page_size=page_size,
            status=ticket_status,
            category=category,
            priority=priority,
            search=search,
            company_id=company_id,
            sort_by=sort_by,
            sort_order=sort_order,
        )
    )

    # Batch-fetch creators for the page
    creator_ids = list({t.created_by for t in tickets})
    users = {
        u.id: u for u in [user_repo.find_by_id(uid) for uid in creator_ids] if u
    }

    return {
        "data": [_to_list_item(t, users) for t in tickets],
        "meta": PaginationMeta(
            page=page, page_size=page_size, total=total
        ).model_dump(),
    }


# NOTE: /stats must be registered BEFORE /{ticket_id} to avoid path conflict
@router.get("/stats")
def get_ticket_stats(
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db),
):
    ticket_repo = SupportTicketRepository(db)
    handler = GetTicketStatsQueryHandler(ticket_repo=ticket_repo)
    stats = handler.handle(GetTicketStatsQuery())
    total = sum(stats.values())
    avg_rating = ticket_repo.get_avg_satisfaction()
    return {
        "data": TicketStatsResponse(
            open=stats.get("open", 0),
            in_progress=stats.get("in_progress", 0),
            waiting_on_customer=stats.get("waiting_on_customer", 0),
            resolved=stats.get("resolved", 0),
            closed=stats.get("closed", 0),
            total=total,
            avg_satisfaction_rating=avg_rating,
        ).model_dump()
    }


@router.get("/{ticket_id}")
def get_ticket_detail(
    ticket_id: str,
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db),
):
    ticket_repo = SupportTicketRepository(db)
    user_repo = UserRepository(db)
    handler = GetTicketDetailQueryHandler(ticket_repo=ticket_repo)
    try:
        detail = handler.handle(
            GetTicketDetailQuery(
                ticket_id=ticket_id,
                company_id=None,  # Super admin — no company scoping
            )
        )
    except TicketNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found"
        )

    # Enrich messages with author info
    author_ids = {m.author_id for m in detail.messages}
    author_ids.add(detail.ticket.created_by)
    users = {
        u.id: u for u in [user_repo.find_by_id(uid) for uid in author_ids] if u
    }

    return {"data": _to_detail_response(detail, users)}


@router.post("/{ticket_id}/messages", status_code=status.HTTP_201_CREATED)
def add_platform_message(
    ticket_id: str,
    body: AddMessageRequest,
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db),
):
    ticket_repo = SupportTicketRepository(db)
    user_repo = UserRepository(db)
    handler = AddTicketMessageCommandHandler(ticket_repo=ticket_repo)
    try:
        handler.handle(
            AddTicketMessageCommand(
                ticket_id=ticket_id,
                author_id=current_user.id,
                body=body.body,
                is_from_platform=True,
                company_id=None,  # Super admin — no company scoping
            )
        )
    except TicketNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found"
        )
    except InvalidTicketTransitionError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(e)
        )
    db.commit()

    # Send email to ticket creator
    ticket = ticket_repo.find_by_id_any_company(ticket_id)
    if ticket:
        creator = user_repo.find_by_id(ticket.created_by)
        if creator:
            send_support_ticket_email.delay(
                to_email=creator.email,
                to_name=creator.name or creator.email,
                ticket_reference=ticket.reference,
                ticket_subject=ticket.subject,
                variant="response_received",
                message_body=body.body,
                responder_name=current_user.name or current_user.email,
            )

    return {"data": {"message": "Message added"}}


@router.patch("/{ticket_id}/status")
def change_ticket_status(
    ticket_id: str,
    body: ChangeStatusRequest,
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db),
):
    ticket_repo = SupportTicketRepository(db)
    user_repo = UserRepository(db)
    handler = ChangeTicketStatusCommandHandler(ticket_repo=ticket_repo)
    try:
        handler.handle(
            ChangeTicketStatusCommand(
                ticket_id=ticket_id,
                new_status=body.status,
            )
        )
    except TicketNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found"
        )
    except InvalidTicketTransitionError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )
    db.commit()

    ticket = ticket_repo.find_by_id_any_company(ticket_id)

    # Send resolved email to ticket creator
    if ticket and body.status == TicketStatus.RESOLVED.value:
        creator = user_repo.find_by_id(ticket.created_by)
        if creator:
            send_support_ticket_email.delay(
                to_email=creator.email,
                to_name=creator.name or creator.email,
                ticket_reference=ticket.reference,
                ticket_subject=ticket.subject,
                variant="ticket_resolved",
            )

    users = {}
    if ticket:
        creator = user_repo.find_by_id(ticket.created_by)
        if creator:
            users[creator.id] = creator

    return {"data": _to_response(ticket, users) if ticket else {}}


@router.patch("/{ticket_id}/priority")
def change_ticket_priority(
    ticket_id: str,
    body: ChangePriorityRequest,
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db),
):
    ticket_repo = SupportTicketRepository(db)
    user_repo = UserRepository(db)
    handler = ChangeTicketPriorityCommandHandler(ticket_repo=ticket_repo)
    try:
        handler.handle(
            ChangeTicketPriorityCommand(
                ticket_id=ticket_id,
                new_priority=body.priority,
            )
        )
    except TicketNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )
    db.commit()

    ticket = ticket_repo.find_by_id_any_company(ticket_id)
    users = {}
    if ticket:
        creator = user_repo.find_by_id(ticket.created_by)
        if creator:
            users[creator.id] = creator

    return {"data": _to_response(ticket, users) if ticket else {}}
