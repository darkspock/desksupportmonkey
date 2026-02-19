from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from src.procurement_bc.purchase_order.domain.entities import (
    PurchaseOrder,
)


class PurchaseOrderRepositoryInterface(ABC):

    @abstractmethod
    def save(self, po: PurchaseOrder) -> PurchaseOrder: ...

    @abstractmethod
    def find_by_id(
        self, po_id: str, company_id: str,
    ) -> Optional[PurchaseOrder]: ...

    @abstractmethod
    def find_by_number(
        self, po_number: str, company_id: str,
    ) -> Optional[PurchaseOrder]: ...

    @abstractmethod
    def find_all(
        self,
        company_id: str,
        page: int,
        page_size: int,
        status: Optional[str] = None,
        vendor_id: Optional[str] = None,
        department_id: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> tuple[list[PurchaseOrder], int]: ...

    @abstractmethod
    def get_next_number(
        self, company_id: str, year: int,
    ) -> int: ...

    @abstractmethod
    def sum_totals_by_department_status(
        self,
        company_id: str,
        department_id: str,
        fiscal_year_start: datetime,
        fiscal_year_end: datetime,
        statuses: list[str],
    ) -> int: ...

    @abstractmethod
    def count_by_department_non_terminal(
        self, company_id: str, department_id: str,
    ) -> int: ...

    @abstractmethod
    def find_by_request_id(
        self, request_id: str, company_id: str,
    ) -> list[PurchaseOrder]: ...
