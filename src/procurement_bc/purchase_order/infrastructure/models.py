from datetime import datetime
from typing import Optional

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.base import Base
from core.mixins import ULIDMixin, TimestampMixin


class PurchaseOrderModel(ULIDMixin, TimestampMixin, Base):
    __tablename__ = "purchase_orders"

    company_id: Mapped[str] = mapped_column(
        String(26),
        ForeignKey("companies.id"),
        index=True,
    )
    po_number: Mapped[str] = mapped_column(String(30))
    vendor_id: Mapped[Optional[str]] = mapped_column(
        String(26),
        ForeignKey("vendors.id"),
        nullable=True,
        index=True,
    )
    vendor_name: Mapped[str] = mapped_column(String(200))
    department_id: Mapped[str] = mapped_column(
        String(26),
        ForeignKey("departments.id"),
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(30), server_default="DRAFT",
    )
    total_amount_cents: Mapped[int] = mapped_column(
        Integer, server_default="0",
    )
    currency: Mapped[str] = mapped_column(
        String(3), server_default="USD",
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
    )
    approved_by: Mapped[Optional[str]] = mapped_column(
        String(26), nullable=True,
    )
    approved_at: Mapped[Optional["datetime"]] = mapped_column(
        DateTime, nullable=True,
    )
    ordered_at: Mapped[Optional["datetime"]] = mapped_column(
        DateTime, nullable=True,
    )
    cancellation_reason: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
    )
    created_by: Mapped[str] = mapped_column(String(26))

    items: Mapped[list["PurchaseOrderItemModel"]] = (
        relationship(
            "PurchaseOrderItemModel",
            cascade="all, delete-orphan",
            lazy="joined",
        )
    )

    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "po_number",
            name="uq_purchase_order_company_number",
        ),
    )


class PurchaseOrderItemModel(ULIDMixin, Base):
    __tablename__ = "purchase_order_items"

    purchase_order_id: Mapped[str] = mapped_column(
        String(26),
        ForeignKey(
            "purchase_orders.id", ondelete="CASCADE",
        ),
        index=True,
    )
    description: Mapped[str] = mapped_column(String(500))
    asset_type: Mapped[Optional[str]] = mapped_column(
        String(30), nullable=True,
    )
    quantity: Mapped[int] = mapped_column(
        Integer, server_default="1",
    )
    unit_cost_cents: Mapped[int] = mapped_column(
        Integer, server_default="0",
    )
    total_cost_cents: Mapped[int] = mapped_column(
        Integer, server_default="0",
    )
    received_quantity: Mapped[int] = mapped_column(
        Integer, server_default="0",
    )
    received_at: Mapped[Optional["datetime"]] = mapped_column(
        DateTime, nullable=True,
    )
    linked_asset_id: Mapped[Optional[str]] = mapped_column(
        String(26), nullable=True,
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
    )


class PurchaseOrderRequestModel(Base):
    __tablename__ = "purchase_order_requests"

    purchase_order_id: Mapped[str] = mapped_column(
        String(26),
        ForeignKey(
            "purchase_orders.id", ondelete="CASCADE",
        ),
        primary_key=True,
    )
    request_id: Mapped[str] = mapped_column(
        String(26),
        ForeignKey("service_requests.id"),
        primary_key=True,
    )
