from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, DateTime, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from core.base import Base
from core.mixins import TimestampMixin, ULIDMixin


class RiskModel(ULIDMixin, TimestampMixin, Base):
    __tablename__ = "risks"

    company_id: Mapped[str] = mapped_column(String(26), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="open"
    )
    likelihood: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    impact: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    risk_level: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    treatment: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    review_cadence: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    next_review_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    owner_id: Mapped[Optional[str]] = mapped_column(String(26), nullable=True)
    created_by: Mapped[str] = mapped_column(String(26), nullable=False)

    __table_args__ = (
        Index("ix_risks_company_status", "company_id", "status"),
        Index("ix_risks_company_level", "company_id", "risk_level"),
        Index("ix_risks_company_category", "company_id", "category"),
        Index("ix_risks_next_review", "next_review_at"),
    )


class MitigationPlanModel(ULIDMixin, TimestampMixin, Base):
    __tablename__ = "mitigation_plans"

    risk_id: Mapped[str] = mapped_column(String(26), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="open"
    )
    owner_id: Mapped[Optional[str]] = mapped_column(String(26), nullable=True)
    target_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    __table_args__ = (Index("ix_mitigation_plans_risk_id", "risk_id"),)


class RiskLinkModel(ULIDMixin, Base):
    __tablename__ = "risk_links"

    risk_id: Mapped[str] = mapped_column(String(26), nullable=False)
    link_type: Mapped[str] = mapped_column(String(20), nullable=False)
    link_id: Mapped[str] = mapped_column(String(26), nullable=False)
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )

    __table_args__ = (
        Index("ix_risk_links_risk_id", "risk_id"),
        UniqueConstraint(
            "risk_id", "link_type", "link_id", name="uq_risk_links_risk_type_entity"
        ),
    )


class RiskHistoryModel(ULIDMixin, Base):
    __tablename__ = "risk_history"

    risk_id: Mapped[str] = mapped_column(String(26), nullable=False)
    event_type: Mapped[str] = mapped_column(String(30), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    actor_id: Mapped[str] = mapped_column(String(26), nullable=False)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )

    __table_args__ = (Index("ix_risk_history_risk_id", "risk_id"),)
