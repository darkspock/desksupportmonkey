from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from src.incident_bc.incident.domain.entities import (
    IncidentTimeline,
    RegulatoryReport,
    SecurityIncident,
)


@dataclass
class IncidentFilters:
    page: int = 1
    page_size: int = 20
    status: Optional[str] = None
    severity: Optional[str] = None
    incident_type: Optional[str] = None
    search: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    custom_field_filters: Optional[dict[str, str]] = None
    custom_field_search_keys: Optional[list[str]] = None


class IncidentRepositoryInterface(ABC):
    # SecurityIncident
    @abstractmethod
    def save(self, incident: SecurityIncident) -> None: ...

    @abstractmethod
    def find_by_id(
        self, incident_id: str, company_id: str
    ) -> Optional[SecurityIncident]: ...

    @abstractmethod
    def find_all(
        self, company_id: str, filters: IncidentFilters
    ) -> tuple[list[SecurityIncident], int]: ...

    # IncidentTimeline
    @abstractmethod
    def save_timeline(self, entry: IncidentTimeline) -> None: ...

    @abstractmethod
    def find_timeline(self, incident_id: str) -> list[IncidentTimeline]: ...

    # IncidentAsset
    @abstractmethod
    def save_incident_asset(
        self,
        incident_id: str,
        asset_id: str,
        impact_description: Optional[str],
    ) -> str: ...

    @abstractmethod
    def delete_incident_asset(self, incident_id: str, asset_id: str) -> None: ...

    @abstractmethod
    def find_assets_by_incident(self, incident_id: str) -> list[dict]: ...

    # IncidentVendor
    @abstractmethod
    def save_incident_vendor(
        self,
        incident_id: str,
        vendor_id: str,
        involvement_description: Optional[str],
    ) -> str: ...

    @abstractmethod
    def delete_incident_vendor(
        self, incident_id: str, vendor_id: str
    ) -> None: ...

    @abstractmethod
    def find_vendors_by_incident(self, incident_id: str) -> list[dict]: ...

    # RegulatoryReport
    @abstractmethod
    def save_report(self, report: RegulatoryReport) -> None: ...

    @abstractmethod
    def save_reports_batch(self, reports: list[RegulatoryReport]) -> None: ...

    @abstractmethod
    def update_report(self, report: RegulatoryReport) -> None: ...

    @abstractmethod
    def find_report_by_id(
        self, report_id: str, incident_id: str
    ) -> Optional[RegulatoryReport]: ...

    @abstractmethod
    def find_reports_by_incident(
        self, incident_id: str
    ) -> list[RegulatoryReport]: ...

    @abstractmethod
    def find_pending_reports_approaching_deadline(
        self,
    ) -> list[tuple[RegulatoryReport, SecurityIncident]]: ...

    # PostMortem
    @abstractmethod
    def save_postmortem(self, postmortem: dict) -> None: ...

    @abstractmethod
    def find_postmortem_by_incident(
        self, incident_id: str
    ) -> Optional[dict]: ...

    # Dashboard
    @abstractmethod
    def get_dashboard_stats(self, company_id: str) -> dict: ...

    # Employee view
    @abstractmethod
    def find_my_incidents(
        self, user_id: str, company_id: str
    ) -> list[SecurityIncident]: ...
