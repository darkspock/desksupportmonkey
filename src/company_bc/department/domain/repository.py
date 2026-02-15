from abc import ABC, abstractmethod
from typing import Optional

from src.company_bc.department.domain.entities import Department


class DepartmentRepositoryInterface(ABC):

    @abstractmethod
    def save(self, department: Department) -> Department: ...

    @abstractmethod
    def find_by_id(self, department_id: str, company_id: str) -> Optional[Department]: ...

    @abstractmethod
    def find_by_name(self, name: str, company_id: str) -> Optional[Department]: ...

    @abstractmethod
    def find_all(
        self, company_id: str, page: int, page_size: int, include_inactive: bool = False
    ) -> tuple[list[Department], int]: ...

    @abstractmethod
    def count_users(self, department_id: str) -> int: ...
