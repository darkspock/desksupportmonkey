from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import ulid


class ApiKeyAlreadyRevokedError(Exception):
    pass


@dataclass
class ApiKey:
    id: str
    user_id: str
    key_hash: str
    name: str
    created_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    is_active: bool = True

    @classmethod
    def create(
        cls,
        user_id: str,
        key_hash: str,
        name: str,
        id: Optional[str] = None,
    ) -> "ApiKey":
        if not name or not name.strip():
            raise ValueError("API key name is required")
        if len(name.strip()) > 100:
            raise ValueError("API key name must be 100 characters or less")
        return cls(
            id=id or str(ulid.new()),
            user_id=user_id,
            key_hash=key_hash,
            name=name.strip(),
        )

    def revoke(self) -> None:
        if not self.is_active:
            raise ApiKeyAlreadyRevokedError(f"API key '{self.id}' is already revoked")
        self.is_active = False
