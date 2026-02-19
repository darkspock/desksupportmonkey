from datetime import date, datetime
from typing import Optional

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from src.appointment_bc.appointment.domain.entities import (
    Appointment,
    AvailabilityOverride,
    TechnicianAvailability,
)
from src.appointment_bc.appointment.domain.enums import (
    AppointmentStatus,
)
from src.appointment_bc.appointment.domain.repository import (
    AppointmentRepositoryInterface,
    AvailabilityOverrideRepositoryInterface,
    TechnicianAvailabilityRepositoryInterface,
)
from src.appointment_bc.appointment.infrastructure.models import (
    AppointmentModel,
    AvailabilityOverrideModel,
    TechnicianAvailabilityModel,
)


class AppointmentRepository(AppointmentRepositoryInterface):

    def __init__(self, session: Session):
        self.session = session

    def save(
        self, appointment: Appointment,
    ) -> Appointment:
        existing = self.session.execute(
            select(AppointmentModel).where(
                AppointmentModel.id == appointment.id,
            )
        ).scalar_one_or_none()

        if existing:
            existing.status = appointment.status.value
            existing.scheduled_start = (
                appointment.scheduled_start
            )
            existing.scheduled_end = (
                appointment.scheduled_end
            )
            existing.duration_minutes = (
                appointment.duration_minutes
            )
            existing.location = appointment.location
            existing.notes = appointment.notes
            existing.cancellation_reason = (
                appointment.cancellation_reason
            )
            existing.cancelled_by = appointment.cancelled_by
            existing.rescheduled_from_id = (
                appointment.rescheduled_from_id
            )
            existing.reminder_24h_sent = (
                appointment.reminder_24h_sent
            )
            existing.reminder_1h_sent = (
                appointment.reminder_1h_sent
            )
            existing.completed_at = appointment.completed_at
        else:
            model = AppointmentModel(
                id=appointment.id,
                company_id=appointment.company_id,
                request_id=appointment.request_id,
                technician_id=appointment.technician_id,
                employee_id=appointment.employee_id,
                status=appointment.status.value,
                scheduled_start=appointment.scheduled_start,
                scheduled_end=appointment.scheduled_end,
                duration_minutes=(
                    appointment.duration_minutes
                ),
                location=appointment.location,
                notes=appointment.notes,
                cancellation_reason=(
                    appointment.cancellation_reason
                ),
                cancelled_by=appointment.cancelled_by,
                rescheduled_from_id=(
                    appointment.rescheduled_from_id
                ),
                reminder_24h_sent=(
                    appointment.reminder_24h_sent
                ),
                reminder_1h_sent=(
                    appointment.reminder_1h_sent
                ),
                completed_at=appointment.completed_at,
                created_by=appointment.created_by,
            )
            self.session.add(model)

        self.session.flush()
        return appointment

    def find_by_id(
        self, appointment_id: str, company_id: str,
    ) -> Optional[Appointment]:
        model = self.session.execute(
            select(AppointmentModel).where(
                AppointmentModel.id == appointment_id,
                AppointmentModel.company_id == company_id,
            )
        ).scalar_one_or_none()
        if not model:
            return None
        return self._to_entity(model)

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
    ) -> tuple[list[Appointment], int]:
        stmt = select(AppointmentModel).where(
            AppointmentModel.company_id == company_id,
        )
        if status:
            stmt = stmt.where(
                AppointmentModel.status == status,
            )
        if technician_id:
            stmt = stmt.where(
                AppointmentModel.technician_id
                == technician_id,
            )
        if employee_id:
            stmt = stmt.where(
                AppointmentModel.employee_id == employee_id,
            )
        if request_id:
            stmt = stmt.where(
                AppointmentModel.request_id == request_id,
            )
        if date_from:
            stmt = stmt.where(
                AppointmentModel.scheduled_start
                >= date_from,
            )
        if date_to:
            stmt = stmt.where(
                AppointmentModel.scheduled_start <= date_to,
            )

        total = self.session.execute(
            select(func.count()).select_from(
                stmt.subquery(),
            )
        ).scalar()

        models = (
            self.session.execute(
                stmt.order_by(
                    AppointmentModel.scheduled_start.desc(),
                )
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
            .scalars()
            .all()
        )

        return [self._to_entity(m) for m in models], (
            total or 0
        )

    def find_by_technician_date_range(
        self,
        technician_id: str,
        company_id: str,
        start: datetime,
        end: datetime,
    ) -> list[Appointment]:
        models = (
            self.session.execute(
                select(AppointmentModel).where(
                    AppointmentModel.technician_id
                    == technician_id,
                    AppointmentModel.company_id
                    == company_id,
                    AppointmentModel.status
                    == AppointmentStatus.CONFIRMED.value,
                    AppointmentModel.scheduled_start < end,
                    AppointmentModel.scheduled_end > start,
                )
            )
            .scalars()
            .all()
        )
        return [self._to_entity(m) for m in models]

    def find_by_employee_date_range(
        self,
        employee_id: str,
        company_id: str,
        start: datetime,
        end: datetime,
    ) -> list[Appointment]:
        models = (
            self.session.execute(
                select(AppointmentModel).where(
                    AppointmentModel.employee_id
                    == employee_id,
                    AppointmentModel.company_id
                    == company_id,
                    AppointmentModel.status
                    == AppointmentStatus.CONFIRMED.value,
                    AppointmentModel.scheduled_start < end,
                    AppointmentModel.scheduled_end > start,
                )
            )
            .scalars()
            .all()
        )
        return [self._to_entity(m) for m in models]

    def find_by_request_id(
        self, request_id: str, company_id: str,
    ) -> list[Appointment]:
        models = (
            self.session.execute(
                select(AppointmentModel).where(
                    AppointmentModel.request_id
                    == request_id,
                    AppointmentModel.company_id
                    == company_id,
                )
            )
            .scalars()
            .all()
        )
        return [self._to_entity(m) for m in models]

    def find_confirmed_before(
        self, before_datetime: datetime,
    ) -> list[Appointment]:
        models = (
            self.session.execute(
                select(AppointmentModel).where(
                    AppointmentModel.status
                    == AppointmentStatus.CONFIRMED.value,
                    AppointmentModel.scheduled_end
                    < before_datetime,
                )
            )
            .scalars()
            .all()
        )
        return [self._to_entity(m) for m in models]

    def find_needing_reminder(
        self,
        reminder_type: str,
        window_start: datetime,
        window_end: datetime,
    ) -> list[Appointment]:
        stmt = select(AppointmentModel).where(
            AppointmentModel.status
            == AppointmentStatus.CONFIRMED.value,
            AppointmentModel.scheduled_start
            >= window_start,
            AppointmentModel.scheduled_start
            <= window_end,
        )
        if reminder_type == "24h":
            stmt = stmt.where(
                AppointmentModel.reminder_24h_sent.is_(
                    False,
                ),
            )
        elif reminder_type == "1h":
            stmt = stmt.where(
                AppointmentModel.reminder_1h_sent.is_(
                    False,
                ),
            )

        models = (
            self.session.execute(stmt).scalars().all()
        )
        return [self._to_entity(m) for m in models]

    def find_pending_or_confirmed_by_request(
        self, request_id: str,
    ) -> list[Appointment]:
        models = (
            self.session.execute(
                select(AppointmentModel).where(
                    AppointmentModel.request_id
                    == request_id,
                    AppointmentModel.status.in_([
                        AppointmentStatus.PENDING.value,
                        AppointmentStatus.CONFIRMED.value,
                    ]),
                )
            )
            .scalars()
            .all()
        )
        return [self._to_entity(m) for m in models]

    @staticmethod
    def _to_entity(
        model: AppointmentModel,
    ) -> Appointment:
        return Appointment(
            id=model.id,
            company_id=model.company_id,
            request_id=model.request_id,
            technician_id=model.technician_id,
            employee_id=model.employee_id,
            status=AppointmentStatus(model.status),
            scheduled_start=model.scheduled_start,
            scheduled_end=model.scheduled_end,
            duration_minutes=model.duration_minutes,
            created_by=model.created_by,
            location=model.location,
            notes=model.notes,
            cancellation_reason=model.cancellation_reason,
            cancelled_by=model.cancelled_by,
            rescheduled_from_id=(
                model.rescheduled_from_id
            ),
            reminder_24h_sent=model.reminder_24h_sent,
            reminder_1h_sent=model.reminder_1h_sent,
            completed_at=model.completed_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


class TechnicianAvailabilityRepository(
    TechnicianAvailabilityRepositoryInterface,
):

    def __init__(self, session: Session):
        self.session = session

    def save_all(
        self,
        technician_id: str,
        company_id: str,
        windows: list[TechnicianAvailability],
    ) -> None:
        # Delete existing windows for this technician
        self.session.execute(
            delete(TechnicianAvailabilityModel).where(
                TechnicianAvailabilityModel.technician_id
                == technician_id,
                TechnicianAvailabilityModel.company_id
                == company_id,
            )
        )
        # Insert new windows
        for w in windows:
            model = TechnicianAvailabilityModel(
                id=w.id,
                company_id=w.company_id,
                technician_id=w.technician_id,
                day_of_week=w.day_of_week,
                start_time=w.start_time,
                end_time=w.end_time,
            )
            self.session.add(model)
        self.session.flush()

    def find_by_technician(
        self, technician_id: str, company_id: str,
    ) -> list[TechnicianAvailability]:
        models = (
            self.session.execute(
                select(
                    TechnicianAvailabilityModel,
                ).where(
                    TechnicianAvailabilityModel.technician_id
                    == technician_id,
                    TechnicianAvailabilityModel.company_id
                    == company_id,
                )
            )
            .scalars()
            .all()
        )
        return [self._to_entity(m) for m in models]

    def find_by_technician_day(
        self,
        technician_id: str,
        company_id: str,
        day_of_week: int,
    ) -> list[TechnicianAvailability]:
        models = (
            self.session.execute(
                select(
                    TechnicianAvailabilityModel,
                ).where(
                    TechnicianAvailabilityModel.technician_id
                    == technician_id,
                    TechnicianAvailabilityModel.company_id
                    == company_id,
                    TechnicianAvailabilityModel.day_of_week
                    == day_of_week,
                )
            )
            .scalars()
            .all()
        )
        return [self._to_entity(m) for m in models]

    @staticmethod
    def _to_entity(
        model: TechnicianAvailabilityModel,
    ) -> TechnicianAvailability:
        return TechnicianAvailability(
            id=model.id,
            company_id=model.company_id,
            technician_id=model.technician_id,
            day_of_week=model.day_of_week,
            start_time=model.start_time,
            end_time=model.end_time,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


class AvailabilityOverrideRepository(
    AvailabilityOverrideRepositoryInterface,
):

    def __init__(self, session: Session):
        self.session = session

    def save(
        self, override: AvailabilityOverride,
    ) -> AvailabilityOverride:
        model = AvailabilityOverrideModel(
            id=override.id,
            company_id=override.company_id,
            technician_id=override.technician_id,
            date=override.date,
            is_available=override.is_available,
            start_time=override.start_time,
            end_time=override.end_time,
            reason=override.reason,
        )
        self.session.add(model)
        self.session.flush()
        return override

    def find_by_id(
        self, override_id: str, company_id: str,
    ) -> Optional[AvailabilityOverride]:
        model = self.session.execute(
            select(AvailabilityOverrideModel).where(
                AvailabilityOverrideModel.id == override_id,
                AvailabilityOverrideModel.company_id
                == company_id,
            )
        ).scalar_one_or_none()
        if not model:
            return None
        return self._to_entity(model)

    def find_by_technician_date_range(
        self,
        technician_id: str,
        company_id: str,
        date_from: date,
        date_to: date,
    ) -> list[AvailabilityOverride]:
        models = (
            self.session.execute(
                select(AvailabilityOverrideModel).where(
                    AvailabilityOverrideModel.technician_id
                    == technician_id,
                    AvailabilityOverrideModel.company_id
                    == company_id,
                    AvailabilityOverrideModel.date
                    >= date_from,
                    AvailabilityOverrideModel.date
                    <= date_to,
                )
            )
            .scalars()
            .all()
        )
        return [self._to_entity(m) for m in models]

    def find_by_technician_date(
        self,
        technician_id: str,
        company_id: str,
        target_date: date,
    ) -> list[AvailabilityOverride]:
        models = (
            self.session.execute(
                select(AvailabilityOverrideModel).where(
                    AvailabilityOverrideModel.technician_id
                    == technician_id,
                    AvailabilityOverrideModel.company_id
                    == company_id,
                    AvailabilityOverrideModel.date
                    == target_date,
                )
            )
            .scalars()
            .all()
        )
        return [self._to_entity(m) for m in models]

    def delete(
        self, override_id: str, company_id: str,
    ) -> bool:
        model = self.session.execute(
            select(AvailabilityOverrideModel).where(
                AvailabilityOverrideModel.id == override_id,
                AvailabilityOverrideModel.company_id
                == company_id,
            )
        ).scalar_one_or_none()
        if not model:
            return False
        self.session.delete(model)
        self.session.flush()
        return True

    @staticmethod
    def _to_entity(
        model: AvailabilityOverrideModel,
    ) -> AvailabilityOverride:
        return AvailabilityOverride(
            id=model.id,
            company_id=model.company_id,
            technician_id=model.technician_id,
            date=model.date,
            is_available=model.is_available,
            start_time=model.start_time,
            end_time=model.end_time,
            reason=model.reason,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
