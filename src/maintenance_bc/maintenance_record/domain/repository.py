from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from src.maintenance_bc.maintenance_record.domain.entities import MaintenanceRecord


class MaintenanceRecordRepositoryInterface(ABC):

    @abstractmethod
    def save(self, record: MaintenanceRecord) -> MaintenanceRecord: ...

    @abstractmethod
    def find_by_id(
        self, record_id: str, company_id: str,
    ) -> Optional[MaintenanceRecord]: ...

    @abstractmethod
    def find_all(
        self,
        company_id: str,
        page: int,
        page_size: int,
        status: Optional[str] = None,
        asset_id: Optional[str] = None,
        technician_id: Optional[str] = None,
        priority: Optional[str] = None,
        scheduled_from: Optional[datetime] = None,
        scheduled_to: Optional[datetime] = None,
        search: Optional[str] = None,
    ) -> tuple[list[MaintenanceRecord], int]: ...

    @abstractmethod
    def find_due_within_hours(
        self, company_id: str, hours: int,
    ) -> list[MaintenanceRecord]: ...

    @abstractmethod
    def find_overdue(
        self, company_id: str,
    ) -> list[MaintenanceRecord]: ...

    @abstractmethod
    def find_my_queue(
        self,
        company_id: str,
        technician_id: str,
        page: int,
        page_size: int,
    ) -> tuple[list[MaintenanceRecord], int]: ...

    @abstractmethod
    def count_dashboard(
        self, company_id: str,
    ) -> dict[str, int]: ...
