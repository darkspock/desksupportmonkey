from typing import Optional

from sqlalchemy import Boolean, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from core.base import Base
from core.mixins import TimestampMixin, ULIDMixin


class AssetTypeDefinitionModel(ULIDMixin, TimestampMixin, Base):
    __tablename__ = "asset_type_definitions"

    company_id: Mapped[str] = mapped_column(String(26), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    icon: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true")
    sort_order: Mapped[int] = mapped_column(Integer, server_default="0")

    __table_args__ = (
        Index("ix_atd_company_active", "company_id", "is_active"),
        UniqueConstraint(
            "company_id",
            "code",
            name="uq_atd_company_code",
        ),
    )
