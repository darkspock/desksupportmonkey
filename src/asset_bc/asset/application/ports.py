from abc import ABC, abstractmethod
from typing import Any, Optional


class UserLookup(ABC):
    """Port for looking up users from asset_bc.

    Satisfied by auth_bc's UserRepository at the router level.
    """

    @abstractmethod
    def find_by_id_and_company(self, user_id: str, company_id: str) -> Optional[Any]:
        """Find a user by ID scoped to a company. Returns None if not found.

        The returned object must have `is_active: bool` and `department_id: Optional[str]`.
        """
        ...
