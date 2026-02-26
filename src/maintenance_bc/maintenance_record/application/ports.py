from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class AssetSummary:
    id: str
    type: str


class AssetLookup(ABC):
    @abstractmethod
    def exists(
        self,
        asset_id: str,
        company_id: str,
    ) -> bool:
        """Return True when the asset exists in the company."""
        ...

    @abstractmethod
    def list_by_company(
        self,
        company_id: str,
    ) -> list[AssetSummary]:
        """Return lightweight assets for maintenance planning."""
        ...


class AssetStatusUpdater(ABC):
    """Port for updating asset status from maintenance_bc.

    Satisfied by asset_bc's repository at the router level.
    """

    @abstractmethod
    def set_status_in_stock(
        self,
        asset_id: str,
        company_id: str,
        performed_by: str,
    ) -> None:
        """Transition asset to IN_STOCK status and create an event."""
        ...


class UserLookup(ABC):
    """Port for looking up users from maintenance_bc.

    Satisfied by auth_bc's UserRepository at the router level.
    """

    @abstractmethod
    def find_by_id_and_company(self, user_id: str, company_id: str) -> Optional[Any]:
        """Find a user by ID scoped to a company. Returns None if not found.

        The returned object must have `is_active: bool`.
        """
        ...
