from abc import ABC, abstractmethod
from typing import Optional

from src.company_bc.employee_role.domain.entities import EmployeeRole


class EmployeeRoleRepositoryInterface(ABC):

    @abstractmethod
    def save(self, role: EmployeeRole) -> EmployeeRole: ...

    @abstractmethod
    def find_by_id(self, role_id: str, company_id: str) -> Optional[EmployeeRole]: ...

    @abstractmethod
    def find_by_name(self, name: str, company_id: str) -> Optional[EmployeeRole]: ...

    @abstractmethod
    def find_all(
        self, company_id: str, page: int, page_size: int, include_inactive: bool = False
    ) -> tuple[list[EmployeeRole], int]: ...

    @abstractmethod
    def delete(self, role_id: str) -> None: ...

    @abstractmethod
    def count_users(self, role_id: str) -> int: ...

    @abstractmethod
    def count_equipment_profiles(self, role_id: str) -> int: ...
