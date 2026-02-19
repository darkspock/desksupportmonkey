from datetime import datetime
from typing import Optional

import ulid
from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func


class ULIDMixin:
    """Mixin that provides a ULID primary key."""

    id: Mapped[str] = mapped_column(String(26), primary_key=True, default=lambda: str(ulid.new()))


class TimestampMixin:
    """Mixin that provides created_at and updated_at timestamps."""

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=func.now(), default=None)
