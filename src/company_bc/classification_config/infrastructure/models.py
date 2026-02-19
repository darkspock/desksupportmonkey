from typing import Optional

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from core.base import Base
from core.mixins import TimestampMixin, ULIDMixin


class ClassificationConfigModel(ULIDMixin, TimestampMixin, Base):
    __tablename__ = "company_classification_configs"

    company_id: Mapped[str] = mapped_column(
        String(26),
        ForeignKey("companies.id"),
        index=True,
    )
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    provider: Mapped[str] = mapped_column(String(20))
    model: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True,
    )
    confidence_threshold: Mapped[float] = mapped_column(Float, default=0.7)
    prompt_template: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
    )
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=10)

    __table_args__ = (
        UniqueConstraint(
            "company_id",
            name="uq_classification_config_company",
        ),
    )
