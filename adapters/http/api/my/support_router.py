import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from adapters.http.api.auth.dependencies import require_role
from adapters.http.api.support.schemas import (
    AddMessageRequest,
    CreateTicketRequest,
    SubmitRatingRequest,
    TicketDetailResponse,
    TicketListItemResponse,
    TicketMessageResponse,
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
from src.support_bc.ticket.application.commands.create_ticket import (
    CreateTicketCommand,
    CreateTicketCommandHandler,
)
from src.support_bc.ticket.application.commands.rate_ticket import (
    RateTicketCommand,
    RateTicketCommandHandler,
)
from src.support_bc.ticket.application.commands.reopen_ticket import (
    ReopenTicketCommand,
    ReopenTicketCommandHandler,
)
from src.support_bc.ticket.application.queries.get_ticket_detail import (
    GetTicketDetailQuery,
    GetTicketDetailQueryHandler,
    TicketDetail,
)
from src.support_bc.ticket.application.queries.list_my_tickets import (
    ListMyTicketsQuery,
    ListMyTicketsQueryHandler,
)
from src.support_bc.ticket.domain.entities import SupportTicket
from src.support_bc.ticket.domain.exceptions import (
    InvalidTicketTransitionError,
    TicketAlreadyRatedError,
    TicketNotFoundError,
    TicketRatingNotAllowedError,
    TicketReopenWindowExpiredError,
)
from src.support_bc.ticket.infrastructure.repository import SupportTicketRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/my/support-tickets", tags=["my-support-tickets"])


def _to_list_item(ticket: SupportTicket) -> dict:
    return TicketListItemResponse(
        id=ticket.id,
        reference=ticket.reference,
        category=ticket.category.value,
        subject=ticket.subject,
        status=ticket.status.value,
        priority=ticket.priority.value,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        resolved_at=ticket.resolved_at,
    ).model_dump(mode="json")


def _to_response(ticket: SupportTicket) -> dict:
    return TicketDetailResponse(
        id=ticket.id,
        reference=ticket.reference,
        company_id=ticket.company_id,
        created_by=ticket.created_by,
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


@router.post("", status_code=status.HTTP_201_CREATED)
def create_ticket(
    body: CreateTicketRequest,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    db: Session = Depends(get_db),
):
    ticket_repo = SupportTicketRepository(db)
    handler = CreateTicketCommandHandler(ticket_repo=ticket_repo)
    try:
        handler.handle(
            CreateTicketCommand(
                company_id=current_user.company_id,
                created_by=current_user.id,
                category=body.category,
                subject=body.subject,
                description=body.description,
                ai_conversation_summary=body.ai_conversation_summary,
            )
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )
    db.commit()

    ticket = handler.created_ticket
    # Send confirmation email to creator
    send_support_ticket_email.delay(
        to_email=current_user.email,
        to_name=current_user.name or current_user.email,
        ticket_reference=ticket.reference,
        ticket_subject=ticket.subject,
        variant="ticket_created",
    )
    # Send notification to support team
    send_support_ticket_email.delay(
        to_email="support@dsmcontrol.com",
        to_name="Support Team",
        ticket_reference=ticket.reference,
        ticket_subject=ticket.subject,
        variant="ticket_created",
    )
    return {"data": _to_response(ticket)}


@router.get("")
def list_my_tickets(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    ticket_status: Optional[str] = Query(None, alias="status"),
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    db: Session = Depends(get_db),
):
    ticket_repo = SupportTicketRepository(db)
    handler = ListMyTicketsQueryHandler(ticket_repo=ticket_repo)
    tickets, total = handler.handle(
        ListMyTicketsQuery(
            user_id=current_user.id,
            company_id=current_user.company_id,
            page=page,
            page_size=page_size,
            status=ticket_status,
        )
    )
    return {
        "data": [_to_list_item(t) for t in tickets],
        "meta": PaginationMeta(
            page=page, page_size=page_size, total=total
        ).model_dump(),
    }


@router.get("/{ticket_id}")
def get_ticket_detail(
    ticket_id: str,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    db: Session = Depends(get_db),
):
    ticket_repo = SupportTicketRepository(db)
    user_repo = UserRepository(db)
    handler = GetTicketDetailQueryHandler(ticket_repo=ticket_repo)
    try:
        detail = handler.handle(
            GetTicketDetailQuery(
                ticket_id=ticket_id,
                company_id=current_user.company_id,
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
def add_message(
    ticket_id: str,
    body: AddMessageRequest,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    db: Session = Depends(get_db),
):
    ticket_repo = SupportTicketRepository(db)
    handler = AddTicketMessageCommandHandler(ticket_repo=ticket_repo)
    try:
        handler.handle(
            AddTicketMessageCommand(
                ticket_id=ticket_id,
                author_id=current_user.id,
                body=body.body,
                is_from_platform=False,
                company_id=current_user.company_id,
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

    # Notify support team
    ticket = ticket_repo.find_by_id(ticket_id, current_user.company_id)
    if ticket:
        send_support_ticket_email.delay(
            to_email="support@dsmcontrol.com",
            to_name="Support Team",
            ticket_reference=ticket.reference,
            ticket_subject=ticket.subject,
            variant="response_received",
            message_body=body.body,
            responder_name=current_user.name or current_user.email,
        )

    return {"data": {"message": "Message added"}}


@router.post("/{ticket_id}/reopen")
def reopen_ticket(
    ticket_id: str,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    db: Session = Depends(get_db),
):
    ticket_repo = SupportTicketRepository(db)
    handler = ReopenTicketCommandHandler(ticket_repo=ticket_repo)
    try:
        handler.handle(
            ReopenTicketCommand(
                ticket_id=ticket_id,
                company_id=current_user.company_id,
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
    except TicketReopenWindowExpiredError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(e)
        )
    db.commit()

    ticket = ticket_repo.find_by_id(ticket_id, current_user.company_id)
    return {"data": _to_response(ticket)}


@router.post("/{ticket_id}/rating", status_code=status.HTTP_201_CREATED)
def submit_rating(
    ticket_id: str,
    body: SubmitRatingRequest,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    db: Session = Depends(get_db),
):
    ticket_repo = SupportTicketRepository(db)
    handler = RateTicketCommandHandler(ticket_repo=ticket_repo)
    try:
        handler.handle(
            RateTicketCommand(
                ticket_id=ticket_id,
                company_id=current_user.company_id,
                user_id=current_user.id,
                rating=body.rating,
                comment=body.comment,
            )
        )
    except TicketNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found"
        )
    except TicketAlreadyRatedError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This ticket has already been rated",
        )
    except TicketRatingNotAllowedError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Rating is only allowed on resolved or closed tickets",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )
    db.commit()

    ticket = ticket_repo.find_by_id(ticket_id, current_user.company_id)
    return {"data": _to_response(ticket)}
