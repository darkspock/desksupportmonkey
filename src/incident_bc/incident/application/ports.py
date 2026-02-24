from abc import ABC, abstractmethod
from typing import Any, Optional


class AssetReader(ABC):
    """Port for reading assets from asset_bc.

    Satisfied by asset_bc's AssetRepository at the router level.
    """

    @abstractmethod
    def find_by_id(self, asset_id: str, company_id: str) -> Optional[Any]:
        """Find an asset by ID scoped to a company. Returns None if not found."""
        ...

    @abstractmethod
    def find_all_by_company(self, company_id: str) -> list[Any]:
        """List all assets for a company."""
        ...


class VendorReader(ABC):
    """Port for reading vendors from procurement_bc.

    Satisfied by procurement_bc's VendorRepository at the router level.
    """

    @abstractmethod
    def find_by_id(self, vendor_id: str, company_id: str) -> Optional[Any]:
        """Find a vendor by ID scoped to a company. Returns None if not found."""
        ...

    @abstractmethod
    def find_all(self, company_id: str) -> list[Any]:
        """List all active vendors for a company."""
        ...
