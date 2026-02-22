from typing import Optional

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from core.base import Base
from core.mixins import ULIDMixin, TimestampMixin


class EmployeeRoleModel(ULIDMixin, TimestampMixin, Base):
    __tablename__ = "employee_roles"

    company_id: Mapped[str] = mapped_column(String(26), ForeignKey("companies.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    __table_args__ = (
        UniqueConstraint("company_id", "name", name="uq_employee_role_company_name"),
    )
