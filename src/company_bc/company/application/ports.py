from abc import ABC, abstractmethod
from typing import Any, Optional


class UserWriter(ABC):
    """Port for user persistence from company_bc.

    Satisfied by auth_bc's UserRepository at the router level.
    """

    @abstractmethod
    def find_by_email(self, email: str) -> Optional[Any]:
        """Find user by email (case-insensitive). Returns None if not found."""
        ...

    @abstractmethod
    def save(self, user: Any) -> Any:
        """Persist a user (insert or update)."""
        ...


class MagicLinkWriter(ABC):
    """Port for magic link persistence from company_bc.

    Satisfied by auth_bc's MagicLinkRepository at the router level.
    """

    @abstractmethod
    def save(self, magic_link: Any) -> Any:
        """Persist a magic link."""
        ...
