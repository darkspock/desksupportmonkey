from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from core.base import Base
from core.mixins import ULIDMixin, TimestampMixin


class SlaEscalationConfigModel(ULIDMixin, TimestampMixin, Base):
    __tablename__ = "company_sla_escalation_configs"

    company_id: Mapped[str] = mapped_column(
        String(26),
        ForeignKey("companies.id"),
        index=True,
    )
    enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
    )

    __table_args__ = (
        UniqueConstraint(
            "company_id",
            name="uq_sla_escalation_config_company",
        ),
    )
