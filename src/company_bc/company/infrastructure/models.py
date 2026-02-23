from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from core.base import Base
from core.mixins import ULIDMixin, TimestampMixin


class CompanyModel(ULIDMixin, TimestampMixin, Base):
    __tablename__ = "companies"

    name: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(20), server_default="active")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Billing fields
    plan: Mapped[str] = mapped_column(String(20), nullable=False, server_default="free")
    billing_status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="active")
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    stripe_subscription_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    grace_period_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    current_period_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    pending_downgrade_plan: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    complimentary: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    trial_ends_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    email_domains = relationship(
        "CompanyEmailDomainModel", backref="company", cascade="all, delete-orphan"
    )


class ProcessedStripeEventModel(Base):
    __tablename__ = "processed_stripe_events"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)  # Stripe event ID
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CompanyEmailDomainModel(ULIDMixin, Base):
    __tablename__ = "company_email_domains"

    company_id: Mapped[str] = mapped_column(String(26), ForeignKey("companies.id"), index=True)
    domain: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
