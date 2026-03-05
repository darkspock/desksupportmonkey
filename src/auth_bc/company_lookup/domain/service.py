from abc import ABC, abstractmethod
from typing import Optional


class CompanyLookupInterface(ABC):
    """Interface for looking up company by email domain."""

    @abstractmethod
    def find_company_id_by_email_domain(self, email: str) -> Optional[str]:
        """Find company_id matching the email domain (active companies only). Returns None if no match."""
        ...

    @abstractmethod
    def find_company_by_email_domain(self, email: str) -> Optional[tuple[str, bool]]:
        """Find (company_id, is_active) for the email domain. Returns None if domain not found."""
        ...

    @abstractmethod
    def is_email_allowed_in_company(self, email: str, company_id: str) -> bool:
        """Check if email is allowed in company (domain mode: email domain match)."""
        ...

    @abstractmethod
    def find_companies_by_email_domain(self, email: str) -> list[tuple[str, str, bool]]:
        """Find ALL companies matching email domain. Returns list of (company_id, slug, is_active)."""
        ...

    @staticmethod
    def extract_domain(email: str) -> str:
        """Extract domain from email address."""
        if "@" not in email:
            raise ValueError(f"Invalid email: {email}")
        return email.split("@")[1].lower().strip()
