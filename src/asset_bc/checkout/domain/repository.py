from abc import ABC, abstractmethod
from typing import Optional

from src.asset_bc.checkout.domain.entities import AssetCheckout


class CheckoutRepositoryInterface(ABC):

    @abstractmethod
    def save(self, checkout: AssetCheckout) -> AssetCheckout: ...

    @abstractmethod
    def find_by_id(self, checkout_id: str, company_id: str) -> Optional[AssetCheckout]: ...

    @abstractmethod
    def find_active_by_asset(self, asset_id: str, company_id: str) -> Optional[AssetCheckout]: ...

    @abstractmethod
    def find_by_asset(
        self,
        asset_id: str,
        company_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[AssetCheckout], int]: ...

    @abstractmethod
    def find_open_by_company(
        self,
        company_id: str,
        page: int = 1,
        page_size: int = 20,
        user_id: Optional[str] = None,
        asset_id: Optional[str] = None,
    ) -> tuple[list[AssetCheckout], int]: ...

    @abstractmethod
    def find_pending_acceptance_by_user(
        self,
        user_id: str,
        company_id: str,
    ) -> list[AssetCheckout]: ...

    @abstractmethod
    def find_open_by_user(
        self,
        user_id: str,
        company_id: str,
    ) -> list[AssetCheckout]: ...

    @abstractmethod
    def count_open_by_company(self, company_id: str) -> int: ...

    @abstractmethod
    def count_pending_acceptance_by_company(self, company_id: str) -> int: ...

    @abstractmethod
    def find_history_by_user(
        self,
        user_id: str,
        company_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[AssetCheckout], int]: ...

    @abstractmethod
    def find_unaccepted_older_than_days(
        self,
        company_id: str,
        days: int,
    ) -> list[AssetCheckout]: ...
