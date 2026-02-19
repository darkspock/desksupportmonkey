from enum import Enum


class MaintenanceStatus(str, Enum):
    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    SKIPPED = "SKIPPED"

    @property
    def is_terminal(self) -> bool:
        return self in {
            MaintenanceStatus.COMPLETED,
            MaintenanceStatus.CANCELLED,
            MaintenanceStatus.SKIPPED,
        }


class MaintenancePriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RecurrenceFrequency(str, Enum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    YEARLY = "YEARLY"


VALID_TRANSITIONS: dict[MaintenanceStatus, list[MaintenanceStatus]] = {
    MaintenanceStatus.SCHEDULED: [
        MaintenanceStatus.IN_PROGRESS,
        MaintenanceStatus.CANCELLED,
        MaintenanceStatus.SKIPPED,
    ],
    MaintenanceStatus.IN_PROGRESS: [
        MaintenanceStatus.COMPLETED,
        MaintenanceStatus.CANCELLED,
    ],
    MaintenanceStatus.COMPLETED: [],
    MaintenanceStatus.CANCELLED: [],
    MaintenanceStatus.SKIPPED: [],
}


class InvalidMaintenanceStatusTransitionError(Exception):
    def __init__(
        self,
        current: MaintenanceStatus,
        target: MaintenanceStatus,
    ):
        self.current = current
        self.target = target
        super().__init__(
            f"Cannot transition from {current.value} to {target.value}"
        )
