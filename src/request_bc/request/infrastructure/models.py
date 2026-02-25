from datetime import datetime
from typing import Any, Optional

from sqlalchemy import DateTime, ForeignKey, Index, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from core.base import Base
from core.mixins import ULIDMixin, TimestampMixin


class ServiceRequestModel(ULIDMixin, TimestampMixin, Base):
    __tablename__ = "service_requests"

    company_id: Mapped[str] = mapped_column(String(26), ForeignKey("companies.id"))
    created_by: Mapped[str] = mapped_column(String(26), ForeignKey("users.id"))
    assigned_to: Mapped[Optional[str]] = mapped_column(String(26), ForeignKey("users.id"))
    type: Mapped[str] = mapped_column(String(30))
    subtype: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), server_default="submitted")
    priority: Mapped[str] = mapped_column(String(10))
    data: Mapped[Optional[Any]] = mapped_column(JSON)
    custom_fields_data: Mapped[Any] = mapped_column(JSON, server_default="{}", nullable=False)
    workflow_template_id: Mapped[Optional[str]] = mapped_column(String(26), nullable=True)
    workflow_subtype_id: Mapped[Optional[str]] = mapped_column(String(26), nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    first_response_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        Index("ix_service_requests_company_status", "company_id", "status"),
        Index("ix_service_requests_company_created_by", "company_id", "created_by"),
        Index("ix_service_requests_company_assigned_to", "company_id", "assigned_to"),
        Index("ix_service_requests_company_subtype", "company_id", "subtype"),
    )


class RequestEventModel(ULIDMixin, Base):
    __tablename__ = "request_events"

    request_id: Mapped[str] = mapped_column(String(26), ForeignKey("service_requests.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(50))
    data: Mapped[Any] = mapped_column(JSON)
    performed_by: Mapped[str] = mapped_column(String(26), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class RequestCommentModel(ULIDMixin, Base):
    __tablename__ = "request_comments"

    request_id: Mapped[str] = mapped_column(String(26), ForeignKey("service_requests.id"), index=True)
    author_id: Mapped[str] = mapped_column(String(26), ForeignKey("users.id"))
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class RequestNoteModel(ULIDMixin, Base):
    __tablename__ = "request_notes"

    request_id: Mapped[str] = mapped_column(String(26), ForeignKey("service_requests.id"), index=True)
    author_id: Mapped[str] = mapped_column(String(26), ForeignKey("users.id"))
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
