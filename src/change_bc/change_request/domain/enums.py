from enum import Enum


class ChangeType(str, Enum):
    STANDARD = "standard"
    NORMAL = "normal"
    EMERGENCY = "emergency"


class ChangeStatus(str, Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    IMPLEMENTED = "implemented"
    CLOSED = "closed"
    REJECTED = "rejected"
    ROLLED_BACK = "rolled_back"

    @property
    def is_terminal(self) -> bool:
        return self in {
            ChangeStatus.CLOSED,
            ChangeStatus.REJECTED,
            ChangeStatus.ROLLED_BACK,
        }


VALID_TRANSITIONS: dict[ChangeStatus, list[ChangeStatus]] = {
    ChangeStatus.DRAFT: [ChangeStatus.PENDING_APPROVAL, ChangeStatus.SCHEDULED],
    ChangeStatus.PENDING_APPROVAL: [ChangeStatus.SCHEDULED, ChangeStatus.REJECTED],
    ChangeStatus.SCHEDULED: [ChangeStatus.IN_PROGRESS],
    ChangeStatus.IN_PROGRESS: [ChangeStatus.IMPLEMENTED, ChangeStatus.ROLLED_BACK],
    ChangeStatus.IMPLEMENTED: [ChangeStatus.CLOSED, ChangeStatus.ROLLED_BACK],
    ChangeStatus.CLOSED: [],
    ChangeStatus.REJECTED: [],
    ChangeStatus.ROLLED_BACK: [],
}


class ChangeEventType(str, Enum):
    CREATED = "created"
    UPDATED = "updated"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    STARTED = "started"
    IMPLEMENTED = "implemented"
    ROLLED_BACK = "rolled_back"
    CLOSED = "closed"
    ASSIGNED = "assigned"
    ASSET_LINKED = "asset_linked"
    ASSET_UNLINKED = "asset_unlinked"
    PIR_ADDED = "pir_added"


class PIROutcome(str, Enum):
    SUCCESSFUL = "successful"
    PARTIAL = "partial"
    FAILED = "failed"


class InvalidStatusTransitionError(Exception):
    def __init__(self, current: ChangeStatus, target: ChangeStatus):
        super().__init__(
            f"Cannot transition from '{current.value}' to '{target.value}'"
        )
        self.current = current
        self.target = target
