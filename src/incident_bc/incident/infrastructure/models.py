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


class SecurityIncidentModel(ULIDMixin, TimestampMixin, Base):
    __tablename__ = "security_incidents"

    company_id: Mapped[str] = mapped_column(String(26), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    incident_type: Mapped[str] = mapped_column(String(30), nullable=False)
    severity: Mapped[str] = mapped_column(String(5), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="detected"
    )
    attack_vector: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True
    )
    data_breach_scope: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reported_by: Mapped[str] = mapped_column(String(26), nullable=False)
    assigned_to: Mapped[Optional[str]] = mapped_column(String(26), nullable=True)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    close_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    closed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        Index("ix_security_incidents_company_status", "company_id", "status"),
        Index("ix_security_incidents_company_severity", "company_id", "severity"),
        Index(
            "ix_security_incidents_company_type", "company_id", "incident_type"
        ),
        Index("ix_security_incidents_detected_at", "detected_at"),
    )


class IncidentTimelineModel(ULIDMixin, Base):
    __tablename__ = "incident_timeline"

    incident_id: Mapped[str] = mapped_column(
        String(26),
        ForeignKey("security_incidents.id"),
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


class IncidentAssetModel(ULIDMixin, Base):
    __tablename__ = "incident_assets"

    incident_id: Mapped[str] = mapped_column(
        String(26),
        ForeignKey("security_incidents.id"),
        nullable=False,
        index=True,
    )
    asset_id: Mapped[str] = mapped_column(String(26), nullable=False)
    impact_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("incident_id", "asset_id", name="uq_incident_asset"),
    )


class IncidentVendorModel(ULIDMixin, Base):
    __tablename__ = "incident_vendors"

    incident_id: Mapped[str] = mapped_column(
        String(26),
        ForeignKey("security_incidents.id"),
        nullable=False,
        index=True,
    )
    vendor_id: Mapped[str] = mapped_column(String(26), nullable=False)
    involvement_description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint(
            "incident_id", "vendor_id", name="uq_incident_vendor"
        ),
    )


class RegulatoryReportModel(ULIDMixin, Base):
    __tablename__ = "regulatory_reports"

    incident_id: Mapped[str] = mapped_column(
        String(26),
        ForeignKey("security_incidents.id"),
        nullable=False,
        index=True,
    )
    report_type: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(
        String(15), nullable=False, server_default="pending"
    )
    deadline_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    generated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    submitted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    file_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    __table_args__ = (
        Index("ix_regulatory_reports_deadline", "deadline_at"),
        Index("ix_regulatory_reports_status", "status"),
    )


class PostMortemModel(ULIDMixin, TimestampMixin, Base):
    __tablename__ = "post_mortems"

    incident_id: Mapped[str] = mapped_column(
        String(26),
        ForeignKey("security_incidents.id"),
        nullable=False,
        unique=True,
    )
    root_cause: Mapped[str] = mapped_column(Text, nullable=False)
    lessons_learned: Mapped[str] = mapped_column(Text, nullable=False)
    corrective_actions: Mapped[str] = mapped_column(Text, nullable=False)
    created_by: Mapped[str] = mapped_column(String(26), nullable=False)
