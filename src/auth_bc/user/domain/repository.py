from abc import ABC, abstractmethod
from typing import Optional

from src.auth_bc.user.domain.entities import User


class UserRepositoryInterface(ABC):
    """Abstract repository for User persistence."""

    @abstractmethod
    def save(self, user: User) -> User:
        """Persist a user (insert or update)."""
        ...

    @abstractmethod
    def find_by_id(self, user_id: str) -> Optional[User]:
        """Find user by ID. Returns None if not found."""
        ...

    @abstractmethod
    def find_by_email(self, email: str) -> Optional[User]:
        """Find user by email (case-insensitive). Returns None if not found."""
        ...

    @abstractmethod
    def find_all_by_company(
        self,
        company_id: str,
        page: int,
        page_size: int,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
        department_id: Optional[str] = None,
        search: Optional[str] = None,
    ) -> tuple[list[User], int]:
        """List users for a company with filters and pagination."""
        ...

    @abstractmethod
    def find_by_id_and_company(self, user_id: str, company_id: str) -> Optional[User]:
        """Find user by ID scoped to a company. Returns None if not found."""
        ...

    @abstractmethod
    def count_by_department(self, department_id: str) -> int:
        """Count active users assigned to a department."""
        ...

    @abstractmethod
    def find_technician_ids_by_company(self, company_id: str) -> list[str]:
        """Find IDs of all active technician+ users in a company."""
        ...
