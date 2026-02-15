import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

import ulid


@dataclass
class MagicLink:
    id: str
    email: str
    token: str
    expires_at: datetime
    used_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    @classmethod
    def create(cls, email: str, ttl_hours: int = 24) -> "MagicLink":
        now = datetime.now(timezone.utc)
        return cls(
            id=str(ulid.new()),
            email=email.lower().strip(),
            token=secrets.token_urlsafe(48),
            expires_at=now + timedelta(hours=ttl_hours),
            created_at=now,
        )

    def mark_used(self) -> None:
        self.used_at = datetime.now(timezone.utc)

    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expires_at.replace(tzinfo=timezone.utc) if self.expires_at.tzinfo is None else datetime.now(timezone.utc) > self.expires_at

    def is_used(self) -> bool:
        return self.used_at is not None
