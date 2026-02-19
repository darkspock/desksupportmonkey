from typing import Optional

from sqlalchemy import Boolean, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from core.base import Base
from core.mixins import ULIDMixin, TimestampMixin


class DepartmentModel(ULIDMixin, TimestampMixin, Base):
    __tablename__ = "departments"

    company_id: Mapped[str] = mapped_column(String(26), ForeignKey("companies.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    manager_user_id: Mapped[Optional[str]] = mapped_column(
        String(26),
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
            name="fk_dept_manager_user_id",
            use_alter=True,
        ),
        nullable=True,
    )
    priority_weight: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")

    __table_args__ = (
        UniqueConstraint("company_id", "name", name="uq_department_company_name"),
    )
