from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from src.sla_bc.sla.domain.entities import SlaBreachRecord, SlaPolicy


class SlaRepositoryInterface(ABC):
    # --- Policies ---

    @abstractmethod
    def save_policy(self, policy: SlaPolicy) -> None:
        ...

    @abstractmethod
    def find_policy_by_id(
        self, policy_id: str, company_id: str
    ) -> Optional[SlaPolicy]:
        ...

    @abstractmethod
    def find_policies(
        self, company_id: str, is_active: Optional[bool] = None
    ) -> list[SlaPolicy]:
        ...

    @abstractmethod
    def find_policy_for_request(
        self, company_id: str, priority: str, request_type: Optional[str] = None
    ) -> Optional[SlaPolicy]:
        ...

    @abstractmethod
    def find_active_policy_by_scope(
        self,
        company_id: str,
        priority: str,
        request_type: Optional[str],
    ) -> Optional[SlaPolicy]:
        ...

    # --- Breach Records ---

    @abstractmethod
    def save_breach(self, breach: SlaBreachRecord) -> None:
        ...

    @abstractmethod
    def find_breaches_for_request(
        self, request_id: str, company_id: str
    ) -> list[SlaBreachRecord]:
        ...

    @abstractmethod
    def has_breach_of_type(
        self, request_id: str, breach_type: str
    ) -> bool:
        ...

    @abstractmethod
    def find_breaches(
        self,
        company_id: str,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[SlaBreachRecord], int]:
        ...

    # --- Dashboard / Stats ---

    @abstractmethod
    def compliance_stats(
        self, company_id: str, from_date: datetime, to_date: datetime
    ) -> dict:
        ...

    @abstractmethod
    def compliance_by_priority(
        self, company_id: str, from_date: datetime, to_date: datetime
    ) -> list[dict]:
        ...

    @abstractmethod
    def compliance_by_type(
        self, company_id: str, from_date: datetime, to_date: datetime
    ) -> list[dict]:
        ...

    @abstractmethod
    def breach_trend(
        self,
        company_id: str,
        from_date: datetime,
        to_date: datetime,
        bucket: str = "week",
    ) -> list[dict]:
        ...
