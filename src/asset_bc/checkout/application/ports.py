from abc import ABC, abstractmethod
from typing import Any, Optional


class CheckoutUserLookup(ABC):
    """Port for looking up users from checkout subdomain.

    Satisfied by auth_bc's UserRepository at the router level.
    """

    @abstractmethod
    def find_by_id_and_company(self, user_id: str, company_id: str) -> Optional[Any]:
        """Find a user by ID scoped to a company.

        The returned object must have `is_active: bool` and `department_id: Optional[str]`.
        """
        ...


class MaintenanceRecordCreator(ABC):
    """Port for creating maintenance records from checkout subdomain.

    Satisfied by maintenance_bc's CreateMaintenanceRecordCommandHandler at the router level.
    """

    @abstractmethod
    def create(
        self,
        record_id: str,
        company_id: str,
        asset_id: str,
        title: str,
        created_by: str,
        priority: str = "HIGH",
        description: Optional[str] = None,
        source_type: Optional[str] = None,
    ) -> None:
        ...
