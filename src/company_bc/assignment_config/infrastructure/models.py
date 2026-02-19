from typing import Optional

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from core.base import Base
from core.mixins import ULIDMixin, TimestampMixin


class AssignmentAIConfigModel(
    ULIDMixin, TimestampMixin, Base,
):
    __tablename__ = "company_assignment_ai_configs"

    company_id: Mapped[str] = mapped_column(
        String(26),
        ForeignKey("companies.id"),
        index=True,
    )
    provider: Mapped[str] = mapped_column(String(20))
    prompt_template: Mapped[str] = mapped_column(Text)
    model: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True,
    )

    __table_args__ = (
        UniqueConstraint(
            "company_id",
            name="uq_assignment_ai_config_company",
        ),
    )
