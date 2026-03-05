from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base
from core.mixins import TimestampMixin, ULIDMixin


class SupportTicketModel(ULIDMixin, TimestampMixin, Base):
    __tablename__ = "support_tickets"

    reference: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    company_id: Mapped[str] = mapped_column(
        String(26), ForeignKey("companies.id"), nullable=False
    )
    created_by: Mapped[str] = mapped_column(
        String(26), ForeignKey("users.id"), nullable=False
    )
    category: Mapped[str] = mapped_column(String(30), nullable=False)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(30), server_default="open", nullable=False
    )
    priority: Mapped[str] = mapped_column(
        String(20), server_default="medium", nullable=False
    )
    ai_conversation_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    satisfaction_rating: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    satisfaction_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    rated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        Index("ix_support_tickets_company_status", "company_id", "status"),
        Index("ix_support_tickets_created_by", "company_id", "created_by"),
        Index("ix_support_tickets_status_priority", "status", "priority"),
    )


class TicketMessageModel(ULIDMixin, Base):
    __tablename__ = "ticket_messages"

    ticket_id: Mapped[str] = mapped_column(
        String(26), ForeignKey("support_tickets.id"), nullable=False
    )
    author_id: Mapped[str] = mapped_column(
        String(26), ForeignKey("users.id"), nullable=False
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
    is_from_platform: Mapped[bool] = mapped_column(
        Boolean, server_default="false", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (Index("ix_ticket_messages_ticket_id", "ticket_id"),)
