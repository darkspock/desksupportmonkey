from enum import Enum


class AppointmentStatus(str, Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    NO_SHOW = "NO_SHOW"

    @property
    def is_terminal(self) -> bool:
        return self in (
            AppointmentStatus.COMPLETED,
            AppointmentStatus.CANCELLED,
            AppointmentStatus.NO_SHOW,
        )


VALID_TRANSITIONS: dict[
    AppointmentStatus, list[AppointmentStatus]
] = {
    AppointmentStatus.PENDING: [
        AppointmentStatus.CONFIRMED,
        AppointmentStatus.CANCELLED,
    ],
    AppointmentStatus.CONFIRMED: [
        AppointmentStatus.COMPLETED,
        AppointmentStatus.CANCELLED,
        AppointmentStatus.NO_SHOW,
    ],
    AppointmentStatus.COMPLETED: [],
    AppointmentStatus.CANCELLED: [],
    AppointmentStatus.NO_SHOW: [],
}


class InvalidAppointmentStatusTransitionError(Exception):
    def __init__(
        self,
        current: AppointmentStatus,
        target: AppointmentStatus,
    ):
        self.current = current
        self.target = target
        super().__init__(
            f"Cannot transition from {current.value} "
            f"to {target.value}"
        )
