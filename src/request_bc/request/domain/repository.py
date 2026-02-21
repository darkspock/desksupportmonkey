from abc import ABC, abstractmethod
from datetime import date
from typing import Optional

from src.request_bc.request.domain.entities import (
    RequestComment,
    RequestEvent,
    RequestNote,
    ServiceRequest,
)


class RequestRepositoryInterface(ABC):

    @abstractmethod
    def save(self, request: ServiceRequest) -> ServiceRequest: ...

    @abstractmethod
    def find_by_id(self, request_id: str, company_id: str) -> Optional[ServiceRequest]: ...

    @abstractmethod
    def save_event(self, event: RequestEvent) -> RequestEvent: ...

    @abstractmethod
    def find_events(self, request_id: str, company_id: str) -> list[RequestEvent]: ...

    @abstractmethod
    def count_comments(self, request_id: str) -> int: ...

    @abstractmethod
    def find_all(
        self,
        company_id: str,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        status: Optional[str] = None,
        type: Optional[str] = None,
        priority: Optional[str] = None,
        assigned_to: Optional[str] = None,
        subtype: Optional[str] = None,
    ) -> tuple[list[ServiceRequest], int]: ...

    @abstractmethod
    def find_by_created_by(
        self,
        user_id: str,
        company_id: str,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        subtype: Optional[str] = None,
    ) -> tuple[list[ServiceRequest], int]: ...

    @abstractmethod
    def save_comment(self, comment: RequestComment) -> RequestComment: ...

    @abstractmethod
    def find_comments(self, request_id: str) -> list[RequestComment]: ...

    @abstractmethod
    def save_note(self, note: RequestNote) -> RequestNote: ...

    @abstractmethod
    def find_notes(self, request_id: str) -> list[RequestNote]: ...

    @abstractmethod
    def count_by_status(self, company_id: str) -> dict[str, int]: ...

    @abstractmethod
    def count_by_type(self, company_id: str) -> dict[str, int]: ...

    @abstractmethod
    def count_by_priority(self, company_id: str) -> dict[str, int]: ...

    @abstractmethod
    def avg_resolution_time(
        self, company_id: str, from_date: Optional[date] = None, to_date: Optional[date] = None
    ) -> Optional[float]: ...

    @abstractmethod
    def avg_resolution_time_by_technician(
        self, company_id: str, from_date: Optional[date] = None, to_date: Optional[date] = None
    ) -> list[dict]: ...

    @abstractmethod
    def count_by_period(
        self, company_id: str, bucket: str, from_date: date, to_date: date
    ) -> list[dict]: ...

    @abstractmethod
    def find_open_requests_with_age(self, company_id: str) -> list[dict]: ...
