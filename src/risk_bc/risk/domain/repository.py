from abc import ABC, abstractmethod
from typing import Optional

from src.risk_bc.risk.domain.entities import (
    MitigationPlan,
    Risk,
    RiskHistory,
    RiskLink,
)


class RiskRepositoryInterface(ABC):
    @abstractmethod
    def save(self, risk: Risk) -> None: ...

    @abstractmethod
    def find_by_id(self, risk_id: str, company_id: str) -> Optional[Risk]: ...

    @abstractmethod
    def find_all(
        self, company_id: str, filters: dict
    ) -> tuple[list[Risk], int]: ...

    @abstractmethod
    def delete(self, risk_id: str, company_id: str) -> None: ...

    @abstractmethod
    def add_history(self, entry: RiskHistory) -> None: ...

    @abstractmethod
    def get_history(self, risk_id: str) -> list[RiskHistory]: ...

    @abstractmethod
    def save_mitigation(self, plan: MitigationPlan) -> None: ...

    @abstractmethod
    def find_mitigation_by_id(
        self, mitigation_id: str, risk_id: str
    ) -> Optional[MitigationPlan]: ...

    @abstractmethod
    def get_mitigations(self, risk_id: str) -> list[MitigationPlan]: ...

    @abstractmethod
    def delete_mitigation(self, mitigation_id: str, risk_id: str) -> None: ...

    @abstractmethod
    def add_link(self, link: RiskLink) -> None: ...

    @abstractmethod
    def get_links(self, risk_id: str) -> list[RiskLink]: ...

    @abstractmethod
    def delete_link(self, link_id: str, risk_id: str) -> None: ...

    @abstractmethod
    def get_dashboard_stats(self, company_id: str) -> dict: ...

    @abstractmethod
    def find_overdue_reviews(
        self, company_id: Optional[str] = None
    ) -> list[Risk]: ...
