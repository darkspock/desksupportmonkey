from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from core.base import Base
from core.mixins import ULIDMixin


class ResellerInvitationModel(ULIDMixin, Base):
    __tablename__ = "reseller_invitations"

    reseller_id: Mapped[str] = mapped_column(String(26), ForeignKey("resellers.id"), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="pending")
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("ix_reseller_invitations_email_status", "email", "status"),
        Index(
            "uq_reseller_invitation_pending",
            "reseller_id",
            "email",
            unique=True,
            postgresql_where=(status == "pending"),
        ),
    )
