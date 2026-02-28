from datetime import datetime
from typing import Optional

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from core.base import Base
from core.mixins import TimestampMixin, ULIDMixin


class ChangeRequestModel(ULIDMixin, TimestampMixin, Base):
    __tablename__ = "change_requests"

    company_id: Mapped[str] = mapped_column(String(26), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    change_type: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="draft"
    )
    business_justification: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    risk_assessment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rollback_plan: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    planned_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    requested_by: Mapped[str] = mapped_column(String(26), nullable=False)
    assigned_to: Mapped[Optional[str]] = mapped_column(String(26), nullable=True)
    approved_by: Mapped[Optional[str]] = mapped_column(String(26), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    rejected_by: Mapped[Optional[str]] = mapped_column(String(26), nullable=True)
    rejected_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    implemented_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    implementation_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rolled_back_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    rollback_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    closed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        Index("ix_change_requests_company_status", "company_id", "status"),
        Index("ix_change_requests_company_type", "company_id", "change_type"),
        Index("ix_change_requests_planned_date", "planned_date"),
    )


class ChangeEventModel(ULIDMixin, Base):
    __tablename__ = "change_events"

    change_request_id: Mapped[str] = mapped_column(
        String(26),
        ForeignKey("change_requests.id"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(String(30), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    actor_id: Mapped[str] = mapped_column(String(26), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)


class ChangeAssetModel(ULIDMixin, Base):
    __tablename__ = "change_assets"

    change_request_id: Mapped[str] = mapped_column(
        String(26),
        ForeignKey("change_requests.id"),
        nullable=False,
        index=True,
    )
    asset_id: Mapped[str] = mapped_column(String(26), nullable=False)
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=True
    )

    __table_args__ = (
        UniqueConstraint(
            "change_request_id",
            "asset_id",
            name="uq_change_assets_change_asset",
        ),
        Index("ix_change_assets_asset_id", "asset_id"),
    )


class PostImplementationReviewModel(ULIDMixin, Base):
    __tablename__ = "post_implementation_reviews"

    change_request_id: Mapped[str] = mapped_column(
        String(26),
        ForeignKey("change_requests.id"),
        nullable=False,
    )
    outcome: Mapped[str] = mapped_column(String(20), nullable=False)
    issues_found: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    lessons_learned: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    follow_up_actions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(String(26), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("change_request_id", name="uq_pir_change_request"),
    )
