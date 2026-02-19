from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import Optional

from src.appointment_bc.appointment.domain.entities import (
    Appointment,
    AvailabilityOverride,
    TechnicianAvailability,
)


class AppointmentRepositoryInterface(ABC):

    @abstractmethod
    def save(
        self, appointment: Appointment,
    ) -> Appointment: ...

    @abstractmethod
    def find_by_id(
        self, appointment_id: str, company_id: str,
    ) -> Optional[Appointment]: ...

    @abstractmethod
    def find_all(
        self,
        company_id: str,
        page: int,
        page_size: int,
        status: Optional[str] = None,
        technician_id: Optional[str] = None,
        employee_id: Optional[str] = None,
        request_id: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> tuple[list[Appointment], int]: ...

    @abstractmethod
    def find_by_technician_date_range(
        self,
        technician_id: str,
        company_id: str,
        start: datetime,
        end: datetime,
    ) -> list[Appointment]: ...

    @abstractmethod
    def find_by_employee_date_range(
        self,
        employee_id: str,
        company_id: str,
        start: datetime,
        end: datetime,
    ) -> list[Appointment]: ...

    @abstractmethod
    def find_by_request_id(
        self, request_id: str, company_id: str,
    ) -> list[Appointment]: ...

    @abstractmethod
    def find_confirmed_before(
        self, before_datetime: datetime,
    ) -> list[Appointment]: ...

    @abstractmethod
    def find_needing_reminder(
        self,
        reminder_type: str,
        window_start: datetime,
        window_end: datetime,
    ) -> list[Appointment]: ...

    @abstractmethod
    def find_pending_or_confirmed_by_request(
        self, request_id: str,
    ) -> list[Appointment]: ...


class TechnicianAvailabilityRepositoryInterface(ABC):

    @abstractmethod
    def save_all(
        self,
        technician_id: str,
        company_id: str,
        windows: list[TechnicianAvailability],
    ) -> None: ...

    @abstractmethod
    def find_by_technician(
        self, technician_id: str, company_id: str,
    ) -> list[TechnicianAvailability]: ...

    @abstractmethod
    def find_by_technician_day(
        self,
        technician_id: str,
        company_id: str,
        day_of_week: int,
    ) -> list[TechnicianAvailability]: ...


class AvailabilityOverrideRepositoryInterface(ABC):

    @abstractmethod
    def save(
        self, override: AvailabilityOverride,
    ) -> AvailabilityOverride: ...

    @abstractmethod
    def find_by_id(
        self, override_id: str, company_id: str,
    ) -> Optional[AvailabilityOverride]: ...

    @abstractmethod
    def find_by_technician_date_range(
        self,
        technician_id: str,
        company_id: str,
        date_from: date,
        date_to: date,
    ) -> list[AvailabilityOverride]: ...

    @abstractmethod
    def find_by_technician_date(
        self,
        technician_id: str,
        company_id: str,
        target_date: date,
    ) -> list[AvailabilityOverride]: ...

    @abstractmethod
    def delete(
        self, override_id: str, company_id: str,
    ) -> bool: ...
