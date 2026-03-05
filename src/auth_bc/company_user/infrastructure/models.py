from typing import Optional

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from core.base import Base
from core.mixins import ULIDMixin, TimestampMixin


class CompanyUserModel(ULIDMixin, TimestampMixin, Base):
    __tablename__ = "company_users"
    __table_args__ = (
        UniqueConstraint("user_id", "company_id", name="uq_company_users_user_company"),
    )

    user_id: Mapped[str] = mapped_column(String(26), ForeignKey("users.id"), nullable=False, index=True)
    company_id: Mapped[str] = mapped_column(String(26), ForeignKey("companies.id"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(30), nullable=False, default="employee")
    department_id: Mapped[Optional[str]] = mapped_column(String(26), ForeignKey("departments.id"), nullable=True)
    employee_role_id: Mapped[Optional[str]] = mapped_column(String(26), ForeignKey("employee_roles.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
