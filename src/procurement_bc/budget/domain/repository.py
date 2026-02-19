from abc import ABC, abstractmethod
from typing import Optional

from src.procurement_bc.budget.domain.entities import (
    CompanyProcurementConfig,
    DepartmentBudget,
)


class DepartmentBudgetRepositoryInterface(ABC):

    @abstractmethod
    def save(
        self, budget: DepartmentBudget,
    ) -> DepartmentBudget: ...

    @abstractmethod
    def find_by_department_year(
        self,
        department_id: str,
        fiscal_year: int,
        company_id: str,
    ) -> Optional[DepartmentBudget]: ...

    @abstractmethod
    def find_all_by_company_year(
        self, company_id: str, fiscal_year: int,
    ) -> list[DepartmentBudget]: ...


class CompanyProcurementConfigRepositoryInterface(ABC):

    @abstractmethod
    def save(
        self, config: CompanyProcurementConfig,
    ) -> CompanyProcurementConfig: ...

    @abstractmethod
    def find_by_company_id(
        self, company_id: str,
    ) -> Optional[CompanyProcurementConfig]: ...
