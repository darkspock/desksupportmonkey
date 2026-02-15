from datetime import datetime
from typing import Optional

import ulid
from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, declared_attr, mapped_column
from sqlalchemy.sql import func


class ULIDMixin:
    """Mixin that provides a ULID primary key."""

    @declared_attr.directive
    @classmethod
    def id(cls) -> Mapped[str]:
        return mapped_column(String(26), primary_key=True, default=lambda: str(ulid.new()))


class TimestampMixin:
    """Mixin that provides created_at and updated_at timestamps."""

    @declared_attr.directive
    @classmethod
    def created_at(cls) -> Mapped[datetime]:
        return mapped_column(DateTime, server_default=func.now())

    @declared_attr.directive
    @classmethod
    def updated_at(cls) -> Mapped[Optional[datetime]]:
        return mapped_column(DateTime, onupdate=func.now(), default=None)
