from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from core.base import Base
from core.mixins import ULIDMixin


class MagicLinkModel(ULIDMixin, Base):
    __tablename__ = "magic_links"

    email: Mapped[str] = mapped_column(String(255), index=True)
    token: Mapped[str] = mapped_column(String(500), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    company_id: Mapped[Optional[str]] = mapped_column(String(26), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
