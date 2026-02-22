from typing import Optional

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.base import Base
from core.mixins import ULIDMixin, TimestampMixin


class EquipmentProfileModel(ULIDMixin, TimestampMixin, Base):
    __tablename__ = "equipment_profiles"

    company_id: Mapped[str] = mapped_column(
        String(26),
        ForeignKey("companies.id"),
        index=True,
    )
    department_id: Mapped[str] = mapped_column(
        String(26),
        ForeignKey("departments.id"),
        index=True,
    )
    employee_role_id: Mapped[Optional[str]] = mapped_column(
        String(26),
        ForeignKey("employee_roles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True,
    )

    items: Mapped[list["EquipmentProfileItemModel"]] = (
        relationship(
            "EquipmentProfileItemModel",
            cascade="all, delete-orphan",
            lazy="joined",
        )
    )

    __table_args__ = (
        Index(
            "ix_equipment_profile_active_unique",
            "company_id",
            "department_id",
            "employee_role_id",
            unique=True,
            postgresql_where=(is_active.is_(True)),
        ),
    )


class EquipmentProfileItemModel(ULIDMixin, Base):
    __tablename__ = "equipment_profile_items"

    profile_id: Mapped[str] = mapped_column(
        String(26),
        ForeignKey(
            "equipment_profiles.id", ondelete="CASCADE",
        ),
        index=True,
    )
    asset_type: Mapped[str] = mapped_column(String(30))
    quantity: Mapped[int] = mapped_column(
        Integer, default=1,
    )
    preferred_brand: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True,
    )
    preferred_model: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True,
    )
    min_ram_gb: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True,
    )
    min_storage_gb: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True,
    )
    budget_cents: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True,
    )
