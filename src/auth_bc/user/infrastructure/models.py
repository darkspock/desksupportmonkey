from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from core.base import Base
from core.mixins import ULIDMixin, TimestampMixin


class UserModel(ULIDMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[Optional[str]] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20))
    company_id: Mapped[Optional[str]] = mapped_column(String(26), ForeignKey("companies.id"), index=True)
    department_id: Mapped[Optional[str]] = mapped_column(String(26), ForeignKey("departments.id"), index=True)
    employee_role_id: Mapped[Optional[str]] = mapped_column(
        String(26),
        ForeignKey("employee_roles.id", ondelete="SET NULL", name="fk_users_employee_role_id"),
        nullable=True,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    email_verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    google_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, unique=True, index=True)
    microsoft_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, unique=True, index=True)
