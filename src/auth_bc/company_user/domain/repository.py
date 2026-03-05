from abc import ABC, abstractmethod
from typing import Optional

from src.auth_bc.company_user.domain.entities import CompanyUser


class CompanyUserRepositoryInterface(ABC):
    """Abstract repository for CompanyUser persistence."""

    @abstractmethod
    def save(self, company_user: CompanyUser) -> CompanyUser:
        """Persist a company user membership (insert or update)."""
        ...

    @abstractmethod
    def find_by_user_and_company(self, user_id: str, company_id: str) -> Optional[CompanyUser]:
        """Find membership for a specific user in a specific company."""
        ...

    @abstractmethod
    def find_by_user_id(self, user_id: str) -> list[CompanyUser]:
        """Find all memberships for a user."""
        ...

    @abstractmethod
    def find_active_by_user_id(self, user_id: str) -> list[CompanyUser]:
        """Find all active memberships for a user."""
        ...

    @abstractmethod
    def find_by_company_id(self, company_id: str) -> list[CompanyUser]:
        """Find all memberships in a company."""
        ...

    @abstractmethod
    def count_admins_in_company(self, company_id: str) -> int:
        """Count active admin memberships in a company."""
        ...

    @abstractmethod
    def count_active_memberships(self, user_id: str) -> int:
        """Count active memberships for a user across all companies."""
        ...
