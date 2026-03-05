from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from src.reseller_bc.client.domain.entities import ResellerClient


class ResellerClientRepositoryInterface(ABC):
    @abstractmethod
    def save(self, client: ResellerClient) -> None: ...

    @abstractmethod
    def get_by_id(self, client_id: str) -> Optional[ResellerClient]: ...

    @abstractmethod
    def find_by_company_id(self, company_id: str) -> Optional[ResellerClient]: ...

    @abstractmethod
    def find_by_reseller_id(self, reseller_id: str, offset: int = 0, limit: int = 50) -> list[ResellerClient]: ...

    @abstractmethod
    def count_by_reseller_id(self, reseller_id: str) -> int: ...

    @abstractmethod
    def count_active_demos_by_reseller_id(self, reseller_id: str) -> int: ...

    @abstractmethod
    def find_expired_demos(self, before: datetime) -> list[ResellerClient]: ...

    @abstractmethod
    def find_purgeable_demos(self, before: datetime) -> list[ResellerClient]: ...
