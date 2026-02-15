from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from src.report_bc.report.domain.entities import Report
from src.report_bc.report.domain.enums import ReportStatus


class ReportRepositoryInterface(ABC):

    @abstractmethod
    def save(self, report: Report) -> Report: ...

    @abstractmethod
    def find_by_id(self, report_id: str, company_id: str) -> Optional[Report]: ...

    @abstractmethod
    def find_by_id_any_company(self, report_id: str) -> Optional[Report]: ...

    @abstractmethod
    def find_all(
        self, company_id: str, page: int = 1, page_size: int = 20
    ) -> tuple[list[Report], int]: ...

    @abstractmethod
    def update_status(
        self,
        report_id: str,
        status: ReportStatus,
        storage_key: Optional[str] = None,
        error_message: Optional[str] = None,
        completed_at: Optional[datetime] = None,
    ) -> bool: ...
