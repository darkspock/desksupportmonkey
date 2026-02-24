from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from core.base import Base
from core.mixins import ULIDMixin


class AuditEntryModel(ULIDMixin, Base):
    __tablename__ = "audit_entries"

    company_id: Mapped[Optional[str]] = mapped_column(
        String(26), nullable=True
    )
    actor_id: Mapped[Optional[str]] = mapped_column(
        String(26), nullable=True
    )
    actor_email: Mapped[str] = mapped_column(
        String(255), nullable=False, server_default=""
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)
    resource_id: Mapped[Optional[str]] = mapped_column(
        String(26), nullable=True
    )
    http_method: Mapped[str] = mapped_column(String(10), nullable=False)
    http_path: Mapped[str] = mapped_column(String(500), nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45), nullable=True
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True
    )
    request_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    response_status: Mapped[int] = mapped_column(Integer, nullable=False)
    changes: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    __table_args__ = (
        Index(
            "ix_audit_entries_company_created",
            "company_id",
            "created_at",
        ),
        Index(
            "ix_audit_entries_company_actor_created",
            "company_id",
            "actor_id",
            "created_at",
        ),
        Index(
            "ix_audit_entries_company_resource",
            "company_id",
            "resource_type",
            "resource_id",
        ),
    )


class ComplianceControlModel(ULIDMixin, Base):
    __tablename__ = "compliance_controls"

    company_id: Mapped[Optional[str]] = mapped_column(
        String(26), ForeignKey("companies.id"), nullable=True
    )
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    framework: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_predefined: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "company_id", "code",
            name="uq_compliance_controls_company_code",
        ),
        Index("ix_compliance_controls_company", "company_id"),
        Index("ix_compliance_controls_framework", "framework"),
    )


class GdprRequestModel(ULIDMixin, Base):
    __tablename__ = "gdpr_requests"

    company_id: Mapped[str] = mapped_column(
        String(26), ForeignKey("companies.id"), nullable=False
    )
    target_user_id: Mapped[str] = mapped_column(
        String(26), ForeignKey("users.id"), nullable=False
    )
    target_user_email: Mapped[str] = mapped_column(
        String(255), nullable=False
    )
    requested_by: Mapped[str] = mapped_column(
        String(26), ForeignKey("users.id"), nullable=False
    )
    request_type: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="pending"
    )
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    storage_key: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    __table_args__ = (
        Index("ix_gdpr_requests_company", "company_id"),
        Index("ix_gdpr_requests_company_status", "company_id", "status"),
        Index("ix_gdpr_requests_target", "target_user_id"),
    )


class RetentionPolicyModel(ULIDMixin, Base):
    __tablename__ = "retention_policies"

    company_id: Mapped[str] = mapped_column(
        String(26), ForeignKey("companies.id"), nullable=False, unique=True
    )
    retention_months: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="36"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    updated_by: Mapped[str] = mapped_column(
        String(26), ForeignKey("users.id"), nullable=False
    )


class ComplianceAssessmentModel(ULIDMixin, Base):
    __tablename__ = "compliance_assessments"

    company_id: Mapped[str] = mapped_column(
        String(26), ForeignKey("companies.id"), nullable=False
    )
    control_id: Mapped[str] = mapped_column(
        String(26), ForeignKey("compliance_controls.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="not_assessed"
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    assessed_by: Mapped[str] = mapped_column(
        String(26), ForeignKey("users.id"), nullable=False
    )
    assessed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "company_id", "control_id",
            name="uq_compliance_assessments_company_control",
        ),
        Index("ix_compliance_assessments_company", "company_id"),
        Index("ix_compliance_assessments_control", "control_id"),
        Index(
            "ix_compliance_assessments_company_status",
            "company_id", "status",
        ),
    )


class ComplianceEvidenceModel(ULIDMixin, Base):
    __tablename__ = "compliance_evidence"

    company_id: Mapped[str] = mapped_column(
        String(26), ForeignKey("companies.id"), nullable=False
    )
    control_id: Mapped[str] = mapped_column(
        String(26), ForeignKey("compliance_controls.id"), nullable=False
    )
    evidence_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )
    reference_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    url: Mapped[Optional[str]] = mapped_column(
        String(1000), nullable=True
    )
    added_by: Mapped[str] = mapped_column(
        String(26), ForeignKey("users.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    __table_args__ = (
        Index("ix_compliance_evidence_control", "control_id"),
        Index("ix_compliance_evidence_company", "company_id"),
    )


class AuditEntryTagModel(ULIDMixin, Base):
    __tablename__ = "audit_entry_tags"

    audit_entry_id: Mapped[str] = mapped_column(
        String(26), ForeignKey("audit_entries.id"), nullable=False
    )
    control_id: Mapped[str] = mapped_column(
        String(26), ForeignKey("compliance_controls.id"), nullable=False
    )
    tagged_by: Mapped[str] = mapped_column(
        String(26), ForeignKey("users.id"), nullable=False
    )
    tagged_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "audit_entry_id", "control_id",
            name="uq_audit_entry_tags_entry_control",
        ),
        Index("ix_audit_entry_tags_entry", "audit_entry_id"),
        Index("ix_audit_entry_tags_control", "control_id"),
    )
