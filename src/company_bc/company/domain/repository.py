from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Optional

from src.company_bc.company.domain.entities import Company



class CompanyRepositoryInterface(ABC):

    @abstractmethod
    def save(self, company: Company) -> Company:
        ...

    @abstractmethod
    def find_by_id(self, company_id: str) -> Optional[Company]:
        ...

    @abstractmethod
    def find_by_name(self, name: str) -> Optional[Company]:
        ...

    @abstractmethod
    def find_all(
        self, page: int, page_size: int, search: Optional[str] = None
    ) -> tuple[list[Company], int]:
        ...

    @abstractmethod
    def find_all_with_counts(
        self,
        page: int,
        page_size: int,
        search: Optional[str] = None,
        in_trial: Optional[bool] = None,
        plan: Optional[str] = None,
    ) -> tuple[list[tuple["Company", int, int]], int]:
        ...

    @abstractmethod
    def find_domain(self, domain: str) -> Optional[str]:
        """Find company_id owning this domain, or None."""
        ...

    @abstractmethod
    def save_domains(self, company_id: str, domains: list[str]) -> None:
        ...

    @abstractmethod
    def count_users(self, company_id: str) -> int:
        ...

    @abstractmethod
    def count_departments(self, company_id: str) -> int:
        ...

    @abstractmethod
    def count_assets(self, company_id: str) -> int:
        ...

    @abstractmethod
    def delete(self, company_id: str) -> None:
        """Delete a company and its email domains."""
        ...

    @abstractmethod
    def get_dashboard_stats(self, now: datetime) -> dict[str, Any]:
        ...

    @abstractmethod
    def find_by_stripe_customer_id(self, customer_id: str) -> Optional[Company]:
        ...

    @abstractmethod
    def mark_stripe_event_processed(self, event_id: str) -> None:
        ...

    @abstractmethod
    def is_stripe_event_processed(self, event_id: str) -> bool:
        ...
