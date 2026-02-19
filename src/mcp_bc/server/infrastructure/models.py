from datetime import datetime
from typing import Optional

import sqlalchemy as sa
from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from core.base import Base
from core.mixins import ULIDMixin


class ApiKeyModel(ULIDMixin, Base):
    __tablename__ = "api_keys"

    user_id: Mapped[str] = mapped_column(String(26), ForeignKey("users.id"), index=True)
    key_hash: Mapped[str] = mapped_column(String(128))
    name: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=None)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=sa.text("true"))
