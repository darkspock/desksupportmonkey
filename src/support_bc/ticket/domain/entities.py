from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import ulid

from src.support_bc.ticket.domain.enums import (
    TicketCategory,
    TicketPriority,
    TicketStatus,
    VALID_TICKET_TRANSITIONS,
)
from src.support_bc.ticket.domain.exceptions import (
    InvalidTicketTransitionError,
    TicketAlreadyRatedError,
    TicketRatingNotAllowedError,
    TicketReopenWindowExpiredError,
)


@dataclass
class SupportTicket:
    id: str
    reference: str  # SUP-NNNN
    company_id: str
    created_by: str
    category: TicketCategory
    subject: str
    description: str
    status: TicketStatus
    priority: TicketPriority
    ai_conversation_summary: Optional[str] = None
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    satisfaction_rating: Optional[int] = None
    satisfaction_comment: Optional[str] = None
    rated_at: Optional[datetime] = None

    REOPEN_WINDOW_DAYS = 7

    @classmethod
    def create(
        cls,
        company_id: str,
        created_by: str,
        category: str,
        subject: str,
        description: str,
        ai_conversation_summary: Optional[str] = None,
        id: Optional[str] = None,
    ) -> "SupportTicket":
        subject = subject.strip()
        description = description.strip()
        if not subject:
            raise ValueError("Subject is required")
        if not description:
            raise ValueError("Description is required")

        return cls(
            id=id or str(ulid.new()),
            reference="",  # Set by repository after sequence nextval
            company_id=company_id,
            created_by=created_by,
            category=TicketCategory(category),
            subject=subject,
            description=description,
            status=TicketStatus.OPEN,
            priority=TicketPriority.MEDIUM,
            ai_conversation_summary=ai_conversation_summary,
        )

    def change_status(self, new_status: TicketStatus) -> None:
        allowed = VALID_TICKET_TRANSITIONS.get(self.status, [])
        if new_status not in allowed:
            raise InvalidTicketTransitionError(
                f"Cannot transition from {self.status.value} to {new_status.value}"
            )
        if new_status == TicketStatus.RESOLVED:
            self.resolved_at = datetime.now(timezone.utc)
        if new_status == TicketStatus.CLOSED:
            self.closed_at = datetime.now(timezone.utc)
        self.status = new_status

    def reopen(self) -> None:
        if self.status != TicketStatus.RESOLVED:
            raise InvalidTicketTransitionError("Only resolved tickets can be reopened")
        if self.resolved_at:
            days_since = (datetime.now(timezone.utc) - self.resolved_at).days
            if days_since > self.REOPEN_WINDOW_DAYS:
                raise TicketReopenWindowExpiredError(
                    "This ticket can no longer be reopened"
                )
        self.status = TicketStatus.OPEN
        self.resolved_at = None

    def change_priority(self, new_priority: TicketPriority) -> None:
        self.priority = new_priority

    def rate(self, rating: int, comment: Optional[str] = None) -> None:
        if self.satisfaction_rating is not None:
            raise TicketAlreadyRatedError("This ticket has already been rated")
        if self.status not in (TicketStatus.RESOLVED, TicketStatus.CLOSED):
            raise TicketRatingNotAllowedError(
                "Rating is only allowed on resolved or closed tickets"
            )
        if not (1 <= rating <= 5):
            raise ValueError("Rating must be between 1 and 5")
        self.satisfaction_rating = rating
        self.satisfaction_comment = comment.strip() if comment else None
        self.rated_at = datetime.now(timezone.utc)


@dataclass
class TicketMessage:
    id: str
    ticket_id: str
    author_id: str
    body: str
    is_from_platform: bool
    created_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        ticket_id: str,
        author_id: str,
        body: str,
        is_from_platform: bool = False,
        id: Optional[str] = None,
    ) -> "TicketMessage":
        body = body.strip()
        if not body:
            raise ValueError("Message body is required")
        return cls(
            id=id or str(ulid.new()),
            ticket_id=ticket_id,
            author_id=author_id,
            body=body,
            is_from_platform=is_from_platform,
        )
