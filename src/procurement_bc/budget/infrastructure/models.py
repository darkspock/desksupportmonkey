from typing import Optional

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from core.base import Base
from core.mixins import ULIDMixin, TimestampMixin


class DepartmentBudgetModel(ULIDMixin, TimestampMixin, Base):
    __tablename__ = "department_budgets"

    company_id: Mapped[str] = mapped_column(
        String(26),
        ForeignKey("companies.id"),
        index=True,
    )
    department_id: Mapped[str] = mapped_column(
        String(26),
        ForeignKey("departments.id"),
    )
    fiscal_year: Mapped[int] = mapped_column(Integer)
    allocated_amount_cents: Mapped[int] = mapped_column(
        Integer, server_default="0",
    )
    currency: Mapped[str] = mapped_column(
        String(3), server_default="USD",
    )

    __table_args__ = (
        UniqueConstraint(
            "department_id",
            "fiscal_year",
            name="uq_budget_department_year",
        ),
    )


class CompanyProcurementConfigModel(
    ULIDMixin, TimestampMixin, Base,
):
    __tablename__ = "company_procurement_configs"

    company_id: Mapped[str] = mapped_column(
        String(26),
        ForeignKey("companies.id"),
        unique=True,
    )
    enforcement_mode: Mapped[str] = mapped_column(
        String(10), server_default="warn",
    )
    approval_threshold_cents: Mapped[int] = mapped_column(
        Integer, server_default="0",
    )
    po_number_prefix: Mapped[str] = mapped_column(
        String(10), server_default="PO",
    )
    fiscal_year_start_month: Mapped[int] = mapped_column(
        Integer, server_default="1",
    )
    currency: Mapped[str] = mapped_column(
        String(3), server_default="USD",
    )
    auto_create_assets: Mapped[bool] = mapped_column(
        Boolean, server_default="false",
    )
