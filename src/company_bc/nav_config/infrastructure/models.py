from typing import Dict, List

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from core.base import Base
from core.mixins import ULIDMixin, TimestampMixin


class NavConfigModel(ULIDMixin, TimestampMixin, Base):
    __tablename__ = "company_nav_configs"

    company_id: Mapped[str] = mapped_column(
        String(26),
        ForeignKey("companies.id"),
        index=True,
    )
    hidden_nav_items: Mapped[Dict[str, List[str]]] = mapped_column(
        JSONB,
        default=dict,
        server_default="{}",
    )

    __table_args__ = (
        UniqueConstraint(
            "company_id",
            name="uq_nav_config_company",
        ),
    )
