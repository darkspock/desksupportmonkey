from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class IncidentSummary:
    id: str
    title: str
    severity: str
    status: str
    created_at: Optional[datetime]


@dataclass
class RiskSummary:
    id: str
    title: str
    risk_level: Optional[str]
    status: str


class IncidentByVendorReader(ABC):
    """Port for reading incidents linked to a vendor from incident_bc.

    Satisfied at the router level by querying incident_bc tables directly.
    """

    @abstractmethod
    def find_by_vendor(
        self,
        vendor_id: str,
        company_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[IncidentSummary], int]:
        """Find incidents linked to a vendor. Returns (items, total)."""
        ...


class RiskByVendorReader(ABC):
    """Port for reading risks linked to a vendor from risk_bc.

    Satisfied at the router level by querying risk_bc tables directly.
    """

    @abstractmethod
    def find_by_vendor(
        self,
        vendor_id: str,
        company_id: str,
    ) -> list[RiskSummary]:
        """Find risks linked to a vendor via RiskLinkType.VENDOR."""
        ...
