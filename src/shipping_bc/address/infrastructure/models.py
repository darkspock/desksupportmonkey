from typing import Optional

from sqlalchemy import (
    Boolean,
    ForeignKey,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from core.base import Base
from core.mixins import ULIDMixin, TimestampMixin


class ShippingAddressModel(ULIDMixin, TimestampMixin, Base):
    __tablename__ = "shipping_addresses"

    company_id: Mapped[str] = mapped_column(
        String(26),
        ForeignKey("companies.id"),
        index=True,
    )
    label: Mapped[str] = mapped_column(String(100))
    recipient_name: Mapped[Optional[str]] = (
        mapped_column(
            String(200), nullable=True,
        )
    )
    street_line_1: Mapped[str] = mapped_column(
        String(300),
    )
    street_line_2: Mapped[Optional[str]] = (
        mapped_column(
            String(300), nullable=True,
        )
    )
    city: Mapped[str] = mapped_column(String(100))
    state: Mapped[str] = mapped_column(String(100))
    postal_code: Mapped[str] = mapped_column(
        String(20),
    )
    country: Mapped[str] = mapped_column(
        String(2), server_default="US",
    )
    phone: Mapped[Optional[str]] = mapped_column(
        String(30), nullable=True,
    )
    user_id: Mapped[Optional[str]] = mapped_column(
        String(26),
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )
    is_office: Mapped[bool] = mapped_column(
        Boolean, server_default="false",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, server_default="true",
    )
