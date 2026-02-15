from abc import ABC, abstractmethod
from typing import Optional

from src.asset_bc.asset.domain.entities import Asset, AssetEvent


class AssetRepositoryInterface(ABC):

    @abstractmethod
    def save(self, asset: Asset) -> Asset: ...

    @abstractmethod
    def find_by_id(self, asset_id: str, company_id: str) -> Optional[Asset]: ...

    @abstractmethod
    def find_by_serial_number(self, serial_number: str, company_id: str) -> Optional[Asset]: ...

    @abstractmethod
    def find_all(
        self, company_id: str, page: int, page_size: int
    ) -> tuple[list[Asset], int]: ...

    @abstractmethod
    def save_event(self, event: AssetEvent) -> AssetEvent: ...

    @abstractmethod
    def find_by_assigned_to(self, user_id: str, company_id: str) -> list[Asset]: ...

    @abstractmethod
    def find_events(self, asset_id: str) -> list[AssetEvent]: ...
