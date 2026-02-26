from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from core.base import Base
from core.mixins import ULIDMixin, TimestampMixin


class AssetCheckoutModel(ULIDMixin, TimestampMixin, Base):
    __tablename__ = "asset_checkouts"

    company_id: Mapped[str] = mapped_column(String(26), ForeignKey("companies.id"), index=True)
    asset_id: Mapped[str] = mapped_column(String(26), ForeignKey("assets.id"), index=True)
    user_id: Mapped[str] = mapped_column(String(26), ForeignKey("users.id"), index=True)
    checked_out_by: Mapped[str] = mapped_column(String(26), ForeignKey("users.id"))
    checked_out_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    condition_out: Mapped[str] = mapped_column(String(20), nullable=False)
    condition_out_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes_out: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    checked_in_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    checked_in_by: Mapped[Optional[str]] = mapped_column(String(26), ForeignKey("users.id"), nullable=True)
    condition_in: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    condition_in_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes_in: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    cancelled_by: Mapped[Optional[str]] = mapped_column(String(26), ForeignKey("users.id"), nullable=True)
    cancel_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    maintenance_id: Mapped[Optional[str]] = mapped_column(String(26), nullable=True)
    auto_assigned: Mapped[bool] = mapped_column(Boolean, server_default="false", nullable=False)

    __table_args__ = (
        Index(
            "uq_asset_checkouts_active",
            "asset_id",
            unique=True,
            postgresql_where=text("checked_in_at IS NULL AND cancelled_at IS NULL"),
        ),
    )
