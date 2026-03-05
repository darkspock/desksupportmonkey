from abc import ABC, abstractmethod
from typing import Optional

from src.reseller_bc.reseller.domain.entities import Reseller


class ResellerRepositoryInterface(ABC):
    """Abstract repository for Reseller persistence."""

    @abstractmethod
    def save(self, reseller: Reseller) -> None:
        """Persist a reseller (insert or update)."""
        ...

    @abstractmethod
    def get_by_id(self, reseller_id: str) -> Optional[Reseller]:
        """Find reseller by ID. Returns None if not found."""
        ...

    @abstractmethod
    def find_by_email(self, email: str) -> Optional[Reseller]:
        """Find reseller by email (case-insensitive). Returns None if not found."""
        ...

    @abstractmethod
    def find_by_google_id(self, google_id: str) -> Optional[Reseller]:
        """Find reseller by Google provider ID. Returns None if not found."""
        ...

    @abstractmethod
    def find_by_microsoft_id(self, microsoft_id: str) -> Optional[Reseller]:
        """Find reseller by Microsoft provider ID. Returns None if not found."""
        ...

    @abstractmethod
    def find_by_referral_code(self, code: str) -> Optional[Reseller]:
        """Find reseller by referral code. Returns None if not found."""
        ...

    @abstractmethod
    def list_all(self, offset: int, limit: int) -> list[Reseller]:
        """List all resellers with pagination."""
        ...

    @abstractmethod
    def count_all(self) -> int:
        """Count all resellers."""
        ...

    @abstractmethod
    def exists_by_email(self, email: str) -> bool:
        """Check if a reseller with this email exists."""
        ...

    @abstractmethod
    def exists_by_referral_code(self, code: str) -> bool:
        """Check if a reseller with this referral code exists."""
        ...

    @abstractmethod
    def find_by_reset_token(self, token: str) -> Optional[Reseller]:
        """Find reseller by password reset token. Returns None if not found."""
        ...
