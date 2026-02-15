from enum import Enum


class RequestType(str, Enum):
    INCIDENT = "incident"
    NEW_EQUIPMENT = "new_equipment"
    ONBOARDING = "onboarding"


class RequestStatus(str, Enum):
    SUBMITTED = "submitted"
    IN_REVIEW = "in_review"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    REJECTED = "rejected"


class RequestPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


VALID_STATUS_TRANSITIONS: dict[RequestStatus, list[RequestStatus]] = {
    RequestStatus.SUBMITTED: [RequestStatus.IN_REVIEW],
    RequestStatus.IN_REVIEW: [RequestStatus.IN_PROGRESS, RequestStatus.REJECTED],
    RequestStatus.IN_PROGRESS: [RequestStatus.RESOLVED, RequestStatus.IN_REVIEW],
    RequestStatus.RESOLVED: [],
    RequestStatus.REJECTED: [],
}

PRIORITY_SORT_ORDER: dict[RequestPriority, int] = {
    RequestPriority.LOW: 1,
    RequestPriority.MEDIUM: 2,
    RequestPriority.HIGH: 3,
    RequestPriority.URGENT: 4,
}

DEFAULT_PRIORITY: dict[RequestType, RequestPriority] = {
    RequestType.INCIDENT: RequestPriority.HIGH,
    RequestType.NEW_EQUIPMENT: RequestPriority.LOW,
    RequestType.ONBOARDING: RequestPriority.MEDIUM,
}


class InvalidStatusTransitionError(Exception):
    def __init__(self, current: RequestStatus, target: RequestStatus):
        self.current = current
        self.target = target
        super().__init__(f"Cannot transition from {current.value} to {target.value}")
