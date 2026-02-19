from src.appointment_bc.appointment.domain.entities import (
    Appointment,
)
from src.notification_bc.notification.domain.enums import (
    EventType,
)
from src.notification_bc.notification.domain.events import (
    DomainEvent,
)


class AppointmentEventFactory:

    @staticmethod
    def appointment_created(
        appointment: Appointment, actor_id: str,
    ) -> DomainEvent:
        return DomainEvent(
            event_type=EventType.APPOINTMENT_CREATED,
            company_id=appointment.company_id,
            actor_id=actor_id,
            payload={
                "appointment_id": appointment.id,
                "request_id": appointment.request_id,
                "technician_id": appointment.technician_id,
                "employee_id": appointment.employee_id,
                "scheduled_start": (
                    appointment.scheduled_start.isoformat()
                ),
            },
            title="Appointment scheduled",
            body=(
                f"Appointment on "
                f"{appointment.scheduled_start:%Y-%m-%d %H:%M} "
                f"for {appointment.duration_minutes} min"
            ),
        )

    @staticmethod
    def appointment_confirmed(
        appointment: Appointment, actor_id: str,
    ) -> DomainEvent:
        return DomainEvent(
            event_type=EventType.APPOINTMENT_CONFIRMED,
            company_id=appointment.company_id,
            actor_id=actor_id,
            payload={
                "appointment_id": appointment.id,
                "request_id": appointment.request_id,
                "technician_id": appointment.technician_id,
                "employee_id": appointment.employee_id,
                "scheduled_start": (
                    appointment.scheduled_start.isoformat()
                ),
            },
            title="Appointment confirmed",
            body=(
                f"Appointment on "
                f"{appointment.scheduled_start:%Y-%m-%d %H:%M} "
                f"confirmed"
            ),
        )

    @staticmethod
    def appointment_cancelled(
        appointment: Appointment, actor_id: str,
    ) -> DomainEvent:
        return DomainEvent(
            event_type=EventType.APPOINTMENT_CANCELLED,
            company_id=appointment.company_id,
            actor_id=actor_id,
            payload={
                "appointment_id": appointment.id,
                "request_id": appointment.request_id,
                "technician_id": appointment.technician_id,
                "employee_id": appointment.employee_id,
                "cancellation_reason": (
                    appointment.cancellation_reason
                ),
            },
            title="Appointment cancelled",
            body=(
                f"Appointment cancelled: "
                f"{appointment.cancellation_reason or 'No reason'}"
            ),
        )

    @staticmethod
    def appointment_rescheduled(
        old_appointment: Appointment,
        new_appointment: Appointment,
        actor_id: str,
    ) -> DomainEvent:
        return DomainEvent(
            event_type=EventType.APPOINTMENT_RESCHEDULED,
            company_id=new_appointment.company_id,
            actor_id=actor_id,
            payload={
                "old_appointment_id": old_appointment.id,
                "new_appointment_id": new_appointment.id,
                "request_id": new_appointment.request_id,
                "technician_id": (
                    new_appointment.technician_id
                ),
                "employee_id": new_appointment.employee_id,
                "old_scheduled_start": (
                    old_appointment.scheduled_start.isoformat()
                ),
                "new_scheduled_start": (
                    new_appointment.scheduled_start.isoformat()
                ),
            },
            title="Appointment rescheduled",
            body=(
                f"Rescheduled to "
                f"{new_appointment.scheduled_start:%Y-%m-%d %H:%M}"
            ),
        )

    @staticmethod
    def appointment_completed(
        appointment: Appointment, actor_id: str,
    ) -> DomainEvent:
        return DomainEvent(
            event_type=EventType.APPOINTMENT_COMPLETED,
            company_id=appointment.company_id,
            actor_id=actor_id,
            payload={
                "appointment_id": appointment.id,
                "request_id": appointment.request_id,
                "technician_id": appointment.technician_id,
                "employee_id": appointment.employee_id,
            },
            title="Appointment completed",
            body="The appointment has been completed",
        )
