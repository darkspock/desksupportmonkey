from abc import ABC, abstractmethod


class UserLookup(ABC):
    """Port for looking up users from notification_bc.

    Satisfied by auth_bc's UserRepository at the router level.
    """

    @abstractmethod
    def find_technician_ids_by_company(self, company_id: str) -> list[str]:
        """Find IDs of all active technician+ users in a company."""
        ...

    @abstractmethod
    def find_admin_ids_by_company(self, company_id: str) -> list[str]:
        """Find IDs of all active admin users in a company."""
        ...
