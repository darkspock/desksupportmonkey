from datetime import datetime
from typing import Optional

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from core.base import Base
from core.mixins import ULIDMixin, TimestampMixin


class ShipmentModel(ULIDMixin, TimestampMixin, Base):
    __tablename__ = "shipments"

    company_id: Mapped[str] = mapped_column(
        String(26),
        ForeignKey("companies.id"),
        index=True,
    )
    direction: Mapped[str] = mapped_column(String(20))
    destination_type: Mapped[str] = mapped_column(
        String(20),
    )
    status: Mapped[str] = mapped_column(
        String(20), server_default="DRAFT",
    )
    origin_address_id: Mapped[Optional[str]] = (
        mapped_column(
            String(26),
            ForeignKey("shipping_addresses.id"),
            nullable=True,
        )
    )
    destination_address_id: Mapped[str] = mapped_column(
        String(26),
        ForeignKey("shipping_addresses.id"),
    )
    recipient_name: Mapped[Optional[str]] = (
        mapped_column(
            String(200), nullable=True,
        )
    )
    recipient_user_id: Mapped[Optional[str]] = (
        mapped_column(
            String(26),
            ForeignKey("users.id"),
            nullable=True,
            index=True,
        )
    )
    carrier: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True,
    )
    service_level: Mapped[Optional[str]] = mapped_column(
        String(40), nullable=True,
    )
    tracking_number: Mapped[Optional[str]] = (
        mapped_column(
            String(100), nullable=True,
        )
    )
    tracking_url: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True,
    )
    items_description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
    )
    internal_notes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
    )
    request_id: Mapped[Optional[str]] = mapped_column(
        String(26),
        ForeignKey("service_requests.id"),
        nullable=True,
        index=True,
    )
    po_id: Mapped[Optional[str]] = mapped_column(
        String(26),
        ForeignKey("purchase_orders.id"),
        nullable=True,
        index=True,
    )
    return_for_shipment_id: Mapped[Optional[str]] = (
        mapped_column(
            String(26),
            ForeignKey("shipments.id"),
            nullable=True,
            index=True,
        )
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
    )
    failure_reason: Mapped[Optional[str]] = (
        mapped_column(
            Text, nullable=True,
        )
    )
    cancellation_reason: Mapped[Optional[str]] = (
        mapped_column(
            Text, nullable=True,
        )
    )
    created_by: Mapped[str] = mapped_column(String(26))
    dispatched_at: Mapped[Optional["datetime"]] = (
        mapped_column(
            DateTime, nullable=True,
        )
    )
    delivered_at: Mapped[Optional["datetime"]] = (
        mapped_column(
            DateTime, nullable=True,
        )
    )

    items: Mapped[list["ShipmentItemModel"]] = (
        relationship(
            "ShipmentItemModel",
            cascade="all, delete-orphan",
            lazy="joined",
        )
    )


class ShipmentItemModel(ULIDMixin, Base):
    __tablename__ = "shipment_items"

    shipment_id: Mapped[str] = mapped_column(
        String(26),
        ForeignKey(
            "shipments.id", ondelete="CASCADE",
        ),
        index=True,
    )
    asset_id: Mapped[str] = mapped_column(
        String(26),
        ForeignKey("assets.id"),
        index=True,
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(),
    )
