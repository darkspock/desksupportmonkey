from typing import Optional

from sqlalchemy import (
    Boolean,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from core.base import Base
from core.mixins import ULIDMixin, TimestampMixin


class VendorModel(ULIDMixin, TimestampMixin, Base):
    __tablename__ = "vendors"

    company_id: Mapped[str] = mapped_column(
        String(26),
        ForeignKey("companies.id"),
        index=True,
    )
    name: Mapped[str] = mapped_column(String(200))
    contact_email: Mapped[Optional[str]] = mapped_column(
        String(254), nullable=True,
    )
    phone: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True,
    )
    address: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, server_default="true",
    )
