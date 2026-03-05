from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from src.reseller_bc.commission.domain.entities import ResellerCommission


class ResellerCommissionRepositoryInterface(ABC):
    @abstractmethod
    def save(self, commission: ResellerCommission) -> None: ...

    @abstractmethod
    def find_by_stripe_invoice_id(self, stripe_invoice_id: str) -> Optional[ResellerCommission]: ...

    @abstractmethod
    def find_by_reseller_id(self, reseller_id: str, offset: int = 0, limit: int = 50) -> list[ResellerCommission]: ...

    @abstractmethod
    def count_by_reseller_id(self, reseller_id: str) -> int: ...

    @abstractmethod
    def find_pending_before(self, before: datetime) -> list[ResellerCommission]: ...

    @abstractmethod
    def sum_confirmed_by_reseller_id(self, reseller_id: str) -> int: ...

    @abstractmethod
    def sum_clawbacks_by_reseller_id(self, reseller_id: str) -> int: ...

    @abstractmethod
    def sum_paid_by_reseller_id(self, reseller_id: str) -> int: ...

    @abstractmethod
    def sum_all_commissions_by_reseller_id(self, reseller_id: str) -> int: ...

    @abstractmethod
    def mark_confirmed_as_paid_for_reseller(self, reseller_id: str) -> int: ...
