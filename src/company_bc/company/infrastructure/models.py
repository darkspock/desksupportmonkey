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

    email_domains = relationship(
        "CompanyEmailDomainModel", backref="company", cascade="all, delete-orphan"
    )


class CompanyEmailDomainModel(ULIDMixin, Base):
    __tablename__ = "company_email_domains"

    company_id: Mapped[str] = mapped_column(String(26), ForeignKey("companies.id"), index=True)
    domain: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
