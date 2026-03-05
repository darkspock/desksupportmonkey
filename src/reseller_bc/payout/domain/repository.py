from abc import ABC, abstractmethod
from typing import Optional

from src.reseller_bc.payout.domain.entities import ResellerPayout


class ResellerPayoutRepositoryInterface(ABC):
    @abstractmethod
    def save(self, payout: ResellerPayout) -> None: ...

    @abstractmethod
    def find_by_id(self, payout_id: str) -> Optional[ResellerPayout]: ...

    @abstractmethod
    def find_by_reseller_id(self, reseller_id: str, offset: int = 0, limit: int = 50) -> list[ResellerPayout]: ...

    @abstractmethod
    def count_by_reseller_id(self, reseller_id: str) -> int: ...

    @abstractmethod
    def find_active_by_reseller_id(self, reseller_id: str) -> Optional[ResellerPayout]: ...

    @abstractmethod
    def find_all(self, offset: int = 0, limit: int = 50, reseller_id: Optional[str] = None) -> list[ResellerPayout]: ...

    @abstractmethod
    def count_all(self, reseller_id: Optional[str] = None) -> int: ...

    @abstractmethod
    def sum_requested_and_approved_by_reseller_id(self, reseller_id: str) -> int: ...
