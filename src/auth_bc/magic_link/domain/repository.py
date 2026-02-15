from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from src.auth_bc.magic_link.domain.entities import MagicLink


class MagicLinkRepositoryInterface(ABC):
    """Abstract repository for MagicLink persistence."""

    @abstractmethod
    def save(self, magic_link: MagicLink) -> MagicLink:
        """Persist a magic link."""
        ...

    @abstractmethod
    def find_by_token(self, token: str) -> Optional[MagicLink]:
        """Find magic link by token. Returns None if not found."""
        ...

    @abstractmethod
    def count_recent_by_email(self, email: str, since: datetime) -> int:
        """Count magic links created for email since given timestamp. Used for rate limiting."""
        ...

    @abstractmethod
    def delete_older_than(self, days: int) -> int:
        """Delete magic links older than N days. Returns count deleted."""
        ...
