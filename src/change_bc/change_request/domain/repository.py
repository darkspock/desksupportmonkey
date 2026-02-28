from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from src.change_bc.change_request.domain.entities import (
    ChangeAsset,
    ChangeEvent,
    ChangeRequest,
    PostImplementationReview,
)


@dataclass
class ChangeRequestFilters:
    page: int = 1
    page_size: int = 20
    status: Optional[str] = None
    change_type: Optional[str] = None
    assigned_to: Optional[str] = None
    search: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


class ChangeRequestRepositoryInterface(ABC):
    @abstractmethod
    def save(self, change: ChangeRequest) -> None: ...

    @abstractmethod
    def find_by_id(
        self, change_id: str, company_id: str
    ) -> Optional[ChangeRequest]: ...

    @abstractmethod
    def find_all(
        self, company_id: str, filters: ChangeRequestFilters
    ) -> tuple[list[ChangeRequest], int]: ...

    @abstractmethod
    def save_event(self, event: ChangeEvent) -> None: ...

    @abstractmethod
    def find_events(self, change_request_id: str) -> list[ChangeEvent]: ...

    # ChangeAsset
    @abstractmethod
    def save_change_asset(self, change_asset: ChangeAsset) -> None: ...

    @abstractmethod
    def delete_change_asset(
        self, change_request_id: str, asset_id: str
    ) -> None: ...

    @abstractmethod
    def find_assets_by_change(
        self, change_request_id: str
    ) -> list[ChangeAsset]: ...

    # Dashboard
    @abstractmethod
    def get_dashboard_data(self, company_id: str) -> dict: ...

    # PostImplementationReview
    @abstractmethod
    def save_pir(self, pir: PostImplementationReview) -> None: ...

    @abstractmethod
    def find_pir_by_change(
        self, change_request_id: str
    ) -> Optional[PostImplementationReview]: ...
