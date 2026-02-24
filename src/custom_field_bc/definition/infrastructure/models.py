from typing import Any, Optional

from sqlalchemy import Boolean, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from core.base import Base
from core.mixins import TimestampMixin, ULIDMixin


class CustomFieldDefinitionModel(ULIDMixin, TimestampMixin, Base):
    __tablename__ = "custom_field_definitions"

    company_id: Mapped[str] = mapped_column(String(26), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(20), nullable=False)
    field_key: Mapped[str] = mapped_column(String(50), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    field_type: Mapped[str] = mapped_column(String(20), nullable=False)
    options: Mapped[Any] = mapped_column(JSON, nullable=True)
    required: Mapped[bool] = mapped_column(Boolean, server_default="false")
    sort_order: Mapped[int] = mapped_column(Integer, server_default="0")
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true")
    visible_to_employees: Mapped[bool] = mapped_column(
        Boolean, server_default="true"
    )

    __table_args__ = (
        Index("ix_cfd_company_entity", "company_id", "entity_type"),
        UniqueConstraint(
            "company_id",
            "entity_type",
            "field_key",
            name="uq_cfd_company_entity_key",
        ),
    )
