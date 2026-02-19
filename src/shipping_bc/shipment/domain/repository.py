from abc import ABC, abstractmethod
from typing import Optional

from src.shipping_bc.shipment.domain.entities import Shipment


class ShipmentRepositoryInterface(ABC):

    @abstractmethod
    def save(self, shipment: Shipment) -> Shipment: ...

    @abstractmethod
    def find_by_id(
        self, shipment_id: str, company_id: str,
    ) -> Optional[Shipment]: ...

    @abstractmethod
    def find_all(
        self,
        company_id: str,
        page: int,
        page_size: int,
        status: Optional[str] = None,
        direction: Optional[str] = None,
        destination_type: Optional[str] = None,
        request_id: Optional[str] = None,
        po_id: Optional[str] = None,
    ) -> tuple[list[Shipment], int]: ...

    @abstractmethod
    def find_by_asset_id(
        self, asset_id: str, company_id: str,
    ) -> list[Shipment]: ...

    @abstractmethod
    def find_active_by_asset_id(
        self, asset_id: str, company_id: str,
    ) -> list[Shipment]: ...

    @abstractmethod
    def find_by_recipient_user_id(
        self,
        recipient_user_id: str,
        company_id: str,
        page: int,
        page_size: int,
    ) -> tuple[list[Shipment], int]: ...

    @abstractmethod
    def count_by_status(
        self, company_id: str,
    ) -> dict[str, int]: ...

    @abstractmethod
    def find_recent_delivered(
        self, company_id: str, days: int,
    ) -> list[Shipment]: ...

    @abstractmethod
    def find_by_status(
        self, company_id: str, status: str,
    ) -> list[Shipment]: ...
