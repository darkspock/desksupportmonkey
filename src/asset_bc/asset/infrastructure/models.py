from datetime import date, datetime
from typing import Any, Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, func, or_
from sqlalchemy.orm import Mapped, mapped_column

from core.base import Base
from core.mixins import ULIDMixin, TimestampMixin


class AssetLocationModel(ULIDMixin, Base):
    __tablename__ = "asset_locations"

    company_id: Mapped[str] = mapped_column(String(26), ForeignKey("companies.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    is_system: Mapped[bool] = mapped_column(Boolean, server_default="false")
    system_key: Mapped[Optional[str]] = mapped_column(String(50))
    in_use: Mapped[bool] = mapped_column(Boolean, server_default="true")
    street_line_1: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    street_line_2: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_personal: Mapped[bool] = mapped_column(Boolean, server_default="false")
    user_id: Mapped[Optional[str]] = mapped_column(String(26), ForeignKey("users.id"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("company_id", "name", name="uq_location_company_name"),
    )


class AssetModel(ULIDMixin, TimestampMixin, Base):
    __tablename__ = "assets"

    company_id: Mapped[str] = mapped_column(String(26), ForeignKey("companies.id"), index=True)
    type: Mapped[str] = mapped_column(String(30))
    brand: Mapped[str] = mapped_column(String(255))
    model: Mapped[str] = mapped_column(String(255))
    serial_number: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(20), server_default="in_stock")
    assigned_to: Mapped[Optional[str]] = mapped_column(String(26), ForeignKey("users.id"), index=True)
    department_id: Mapped[Optional[str]] = mapped_column(String(26), ForeignKey("departments.id"), index=True)
    location_id: Mapped[Optional[str]] = mapped_column(String(26), ForeignKey("asset_locations.id"), index=True)
    purchase_date: Mapped[Optional[date]] = mapped_column(Date)
    warranty_expiration: Mapped[Optional[date]] = mapped_column(Date)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    purchase_cost_cents: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True,
    )
    custom_fields_data: Mapped[Any] = mapped_column(JSON, server_default="{}", nullable=False)
    criticality: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    impact_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    rto_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    rpo_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    bia_justification: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    bia_reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    bia_reviewed_by: Mapped[Optional[str]] = mapped_column(String(26), ForeignKey("users.id"), nullable=True)

    __table_args__ = (
        UniqueConstraint("company_id", "serial_number", name="uq_asset_company_serial"),
    )


class CIRelationshipModel(ULIDMixin, TimestampMixin, Base):
    __tablename__ = "ci_relationships"

    company_id: Mapped[str] = mapped_column(String(26), ForeignKey("companies.id"), index=True)
    source_asset_id: Mapped[str] = mapped_column(String(26), ForeignKey("assets.id"), index=True)
    target_asset_id: Mapped[str] = mapped_column(String(26), ForeignKey("assets.id"), index=True)
    relationship_type: Mapped[str] = mapped_column(String(20))
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_by: Mapped[str] = mapped_column(String(26))
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint(
            "source_asset_id", "target_asset_id", "relationship_type",
            name="uq_ci_rel_source_target_type",
        ),
    )


class AssetEventModel(ULIDMixin, Base):
    __tablename__ = "asset_events"

    asset_id: Mapped[str] = mapped_column(String(26), ForeignKey("assets.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(50))
    data: Mapped[Any] = mapped_column(JSON)
    performed_by: Mapped[str] = mapped_column(String(26), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
