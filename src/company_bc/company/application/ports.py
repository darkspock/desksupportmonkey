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

    @abstractmethod
    def has_any_verified_user_in_company(self, company_id: str) -> bool:
        """Return True if any user in the company has confirmed their email."""
        ...

    @abstractmethod
    def delete_by_company(self, company_id: str) -> None:
        """Delete all users belonging to a company."""
        ...


class CompanyUserWriter(ABC):
    """Port for company_user persistence from company_bc.

    Satisfied by auth_bc's CompanyUserRepository at the router level.
    """

    @abstractmethod
    def save(self, company_user: Any) -> None:
        """Persist a company user membership."""
        ...

    @abstractmethod
    def find_by_user_and_company(
        self, user_id: str, company_id: str
    ) -> Optional[Any]:
        """Find membership for a user in a company."""
        ...


class MagicLinkWriter(ABC):
    """Port for magic link persistence from company_bc.

    Satisfied by auth_bc's MagicLinkRepository at the router level.
    """

    @abstractmethod
    def save(self, magic_link: Any) -> Any:
        """Persist a magic link."""
        ...
