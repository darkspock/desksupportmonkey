from abc import ABC, abstractmethod
from typing import Any, Optional


class DepartmentLookup(ABC):
    """Port for looking up departments from auth_bc.

    Satisfied by company_bc's DepartmentRepository at the router level.
    """

    @abstractmethod
    def find_by_id(self, department_id: str, company_id: str) -> Optional[Any]:
        """Find a department by ID scoped to a company. Returns None if not found.

        The returned object must have `is_active: bool`.
        """
        ...
