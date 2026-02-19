from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from src.maintenance_bc.maintenance_template.domain.entities import (
    MaintenancePlan,
    MaintenanceTemplate,
)


class MaintenanceTemplateRepositoryInterface(ABC):

    @abstractmethod
    def save(
        self, template: MaintenanceTemplate,
    ) -> MaintenanceTemplate: ...

    @abstractmethod
    def find_by_id(
        self, template_id: str, company_id: str,
    ) -> Optional[MaintenanceTemplate]: ...

    @abstractmethod
    def find_all(
        self,
        company_id: str,
        page: int,
        page_size: int,
        is_active: Optional[bool] = None,
    ) -> tuple[list[MaintenanceTemplate], int]: ...

    @abstractmethod
    def find_by_ids(
        self,
        template_ids: list[str],
        company_id: str,
    ) -> dict[str, MaintenanceTemplate]: ...


class MaintenancePlanRepositoryInterface(ABC):

    @abstractmethod
    def save(self, plan: MaintenancePlan) -> MaintenancePlan: ...

    @abstractmethod
    def find_by_id(
        self, plan_id: str, company_id: str,
    ) -> Optional[MaintenancePlan]: ...

    @abstractmethod
    def find_all(
        self,
        company_id: str,
        page: int,
        page_size: int,
        is_active: Optional[bool] = None,
        template_id: Optional[str] = None,
        asset_id: Optional[str] = None,
    ) -> tuple[list[MaintenancePlan], int]: ...

    @abstractmethod
    def find_due_plans(
        self,
        company_id: str,
        due_before: datetime,
    ) -> list[MaintenancePlan]: ...

    @abstractmethod
    def find_active_by_template_asset(
        self,
        company_id: str,
        template_id: str,
        asset_id: str,
    ) -> Optional[MaintenancePlan]: ...
