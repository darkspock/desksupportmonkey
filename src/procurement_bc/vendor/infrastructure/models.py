from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from core.base import Base
from core.mixins import ULIDMixin, TimestampMixin


class VendorModel(ULIDMixin, TimestampMixin, Base):
    __tablename__ = "vendors"

    company_id: Mapped[str] = mapped_column(
        String(26),
        ForeignKey("companies.id"),
        index=True,
    )
    name: Mapped[str] = mapped_column(String(200))
    contact_email: Mapped[Optional[str]] = mapped_column(
        String(254), nullable=True,
    )
    phone: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True,
    )
    address: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, server_default="true",
    )
    # E25 extensions
    is_critical_ict: Mapped[bool] = mapped_column(
        Boolean, server_default="false",
    )
    risk_level: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True,
    )
    website: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True,
    )
    category: Mapped[Optional[str]] = mapped_column(
        String(30), nullable=True,
    )


class VendorContractModel(ULIDMixin, TimestampMixin, Base):
    __tablename__ = "vendor_contracts"

    __table_args__ = (
        Index("ix_vendor_contracts_vendor_company", "vendor_id", "company_id"),
        Index("ix_vendor_contracts_company_status", "company_id", "status"),
    )

    vendor_id: Mapped[str] = mapped_column(
        String(26), ForeignKey("vendors.id"),
    )
    company_id: Mapped[str] = mapped_column(
        String(26), ForeignKey("companies.id"),
    )
    contract_type: Mapped[str] = mapped_column(String(20))
    title: Mapped[str] = mapped_column(String(200))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    renewal_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    auto_renewal: Mapped[bool] = mapped_column(Boolean, server_default="false")
    annual_value: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2), nullable=True,
    )
    currency: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)
    security_clauses: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), server_default="draft")
    is_deleted: Mapped[bool] = mapped_column(Boolean, server_default="false")


class VendorContractDocumentModel(ULIDMixin, Base):
    __tablename__ = "vendor_contract_documents"

    __table_args__ = (
        Index(
            "ix_vendor_contract_docs_contract_company",
            "contract_id", "company_id",
        ),
    )

    contract_id: Mapped[str] = mapped_column(
        String(26), ForeignKey("vendor_contracts.id"),
    )
    company_id: Mapped[str] = mapped_column(
        String(26), ForeignKey("companies.id"),
    )
    filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(100))
    size_bytes: Mapped[int] = mapped_column(Integer)
    storage_key: Mapped[str] = mapped_column(String(500))
    uploaded_by: Mapped[str] = mapped_column(String(26))
    is_deleted: Mapped[bool] = mapped_column(Boolean, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class VendorRiskAssessmentModel(ULIDMixin, TimestampMixin, Base):
    __tablename__ = "vendor_risk_assessments"

    __table_args__ = (
        Index("ix_vendor_risk_assessments_vendor_company", "vendor_id", "company_id"),
        Index("ix_vendor_risk_assessments_company_date", "company_id", "assessment_date"),
    )

    vendor_id: Mapped[str] = mapped_column(
        String(26), ForeignKey("vendors.id"),
    )
    company_id: Mapped[str] = mapped_column(
        String(26), ForeignKey("companies.id"),
    )
    assessed_by: Mapped[str] = mapped_column(String(26))
    assessment_date: Mapped[date] = mapped_column(Date)
    next_review_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    data_handling_score: Mapped[int] = mapped_column(SmallInteger)
    security_certs_score: Mapped[int] = mapped_column(SmallInteger)
    incident_response_score: Mapped[int] = mapped_column(SmallInteger)
    business_continuity_score: Mapped[int] = mapped_column(SmallInteger)
    subcontractor_score: Mapped[int] = mapped_column(SmallInteger)
    overall_risk_level: Mapped[str] = mapped_column(String(20))
    justification: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, server_default="false")


class VendorDependencyModel(ULIDMixin, TimestampMixin, Base):
    __tablename__ = "vendor_dependencies"

    __table_args__ = (
        Index("ix_vendor_dependencies_vendor_company", "vendor_id", "company_id"),
        Index("ix_vendor_dependencies_company_critical", "company_id", "is_critical"),
    )

    vendor_id: Mapped[str] = mapped_column(
        String(26), ForeignKey("vendors.id"),
    )
    company_id: Mapped[str] = mapped_column(
        String(26), ForeignKey("companies.id"),
    )
    service_description: Mapped[str] = mapped_column(String(500))
    business_function: Mapped[str] = mapped_column(String(30))
    is_critical: Mapped[bool] = mapped_column(Boolean, server_default="false")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, server_default="false")
