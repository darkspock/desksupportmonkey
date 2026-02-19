from abc import ABC, abstractmethod
from typing import Optional

from src.shipping_bc.address.domain.entities import ShippingAddress


class ShippingAddressRepositoryInterface(ABC):

    @abstractmethod
    def save(
        self, address: ShippingAddress,
    ) -> ShippingAddress: ...

    @abstractmethod
    def find_by_id(
        self, address_id: str, company_id: str,
    ) -> Optional[ShippingAddress]: ...

    @abstractmethod
    def find_all(
        self,
        company_id: str,
        page: int,
        page_size: int,
        user_id: Optional[str] = None,
        is_office: Optional[bool] = None,
        is_active: Optional[bool] = None,
    ) -> tuple[list[ShippingAddress], int]: ...

    @abstractmethod
    def find_by_user_id(
        self, user_id: str, company_id: str,
    ) -> list[ShippingAddress]: ...
