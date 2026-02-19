from abc import ABC, abstractmethod
from typing import Optional

from src.procurement_bc.vendor.domain.entities import Vendor


class VendorRepositoryInterface(ABC):

    @abstractmethod
    def save(self, vendor: Vendor) -> Vendor: ...

    @abstractmethod
    def find_by_id(
        self, vendor_id: str, company_id: str,
    ) -> Optional[Vendor]: ...

    @abstractmethod
    def find_all(
        self,
        company_id: str,
        page: int,
        page_size: int,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> tuple[list[Vendor], int]: ...

    @abstractmethod
    def find_by_name(
        self, name: str, company_id: str,
    ) -> Optional[Vendor]: ...
