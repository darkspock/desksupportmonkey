from abc import ABC, abstractmethod
from typing import Optional

from src.asset_bc.asset.domain.entities import Asset, AssetEvent, AssetLocation


class AssetRepositoryInterface(ABC):

    @abstractmethod
    def save(self, asset: Asset) -> Asset: ...

    @abstractmethod
    def save_location(self, location: AssetLocation) -> AssetLocation: ...

    @abstractmethod
    def find_location_by_id(self, location_id: str, company_id: str) -> Optional[AssetLocation]: ...

    @abstractmethod
    def find_locations_by_company(self, company_id: str) -> list[AssetLocation]: ...

    @abstractmethod
    def find_system_location(self, company_id: str, system_key: str) -> Optional[AssetLocation]: ...

    @abstractmethod
    def delete_location(self, location_id: str) -> None: ...

    @abstractmethod
    def count_assets_at_location(self, location_id: str) -> int: ...

    @abstractmethod
    def find_location_by_name(self, name: str, company_id: str) -> Optional[AssetLocation]: ...

    @abstractmethod
    def find_by_id(self, asset_id: str, company_id: str) -> Optional[Asset]: ...

    @abstractmethod
    def find_by_serial_number(self, serial_number: str, company_id: str) -> Optional[Asset]: ...

    @abstractmethod
    def find_all(
        self,
        company_id: str,
        page: int,
        page_size: int,
        search: Optional[str] = None,
        type: Optional[str] = None,
        status: Optional[str] = None,
        department_id: Optional[str] = None,
        assigned_to: Optional[str] = None,
        location_id: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[Asset], int]: ...

    @abstractmethod
    def save_event(self, event: AssetEvent) -> AssetEvent: ...

    @abstractmethod
    def find_by_assigned_to(self, user_id: str, company_id: str) -> list[Asset]: ...

    @abstractmethod
    def find_events(self, asset_id: str) -> list[AssetEvent]: ...

    @abstractmethod
    def count_by_status(self, company_id: str) -> dict[str, int]: ...

    @abstractmethod
    def count_by_type(self, company_id: str) -> dict[str, int]: ...

    @abstractmethod
    def find_expiring_warranties(self, company_id: str, days: int) -> list[dict]: ...

    @abstractmethod
    def find_aging_assets(self, company_id: str, years: int) -> list[dict]: ...

    @abstractmethod
    def find_all_by_company(self, company_id: str) -> list[Asset]: ...

    @abstractmethod
    def find_in_stock_by_type(
        self, company_id: str, asset_type: str,
    ) -> list[Asset]: ...
