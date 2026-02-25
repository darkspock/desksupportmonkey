from enum import Enum


class RequestType(str, Enum):
    INCIDENT = "incident"
    NEW_EQUIPMENT = "new_equipment"
    ONBOARDING = "onboarding"
    REPAIR = "repair"
    CONFIGURATION = "configuration"
    ACCESS_REQUEST = "access_request"


class RequestSubtype(str, Enum):
    # Repair subtypes
    HARDWARE = "hardware"
    SOFTWARE = "software"
    NETWORK = "network"
    SECURITY = "security"
    OTHER = "other"
    # New equipment subtypes
    COMPUTER = "computer"
    MOBILE = "mobile"
    PERIPHERAL = "peripheral"
    MONITOR = "monitor"
    SOFTWARE_LICENSE = "software_license"
    # Configuration subtypes
    SOFTWARE_INSTALL = "software_install"
    ACCOUNT_SETUP = "account_setup"
    PERMISSIONS = "permissions"
    # Access request subtypes
    SYSTEM_ACCESS = "system_access"
    PHYSICAL_ACCESS = "physical_access"
    VPN = "vpn"


VALID_SUBTYPES: dict[RequestType, list[RequestSubtype]] = {
    RequestType.INCIDENT: [],
    RequestType.NEW_EQUIPMENT: [
        RequestSubtype.COMPUTER,
        RequestSubtype.MOBILE,
        RequestSubtype.PERIPHERAL,
        RequestSubtype.MONITOR,
        RequestSubtype.SOFTWARE_LICENSE,
    ],
    RequestType.ONBOARDING: [],
    RequestType.REPAIR: [
        RequestSubtype.HARDWARE,
        RequestSubtype.SOFTWARE,
        RequestSubtype.NETWORK,
        RequestSubtype.SECURITY,
        RequestSubtype.OTHER,
    ],
    RequestType.CONFIGURATION: [
        RequestSubtype.SOFTWARE_INSTALL,
        RequestSubtype.ACCOUNT_SETUP,
        RequestSubtype.PERMISSIONS,
    ],
    RequestType.ACCESS_REQUEST: [
        RequestSubtype.SYSTEM_ACCESS,
        RequestSubtype.PHYSICAL_ACCESS,
        RequestSubtype.VPN,
    ],
}


class RequestStatus(str, Enum):
    PENDING_APPROVAL = "pending_approval"
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
    RequestStatus.PENDING_APPROVAL: [RequestStatus.SUBMITTED, RequestStatus.REJECTED],
    RequestStatus.SUBMITTED: [RequestStatus.IN_REVIEW],
    RequestStatus.IN_REVIEW: [RequestStatus.IN_PROGRESS, RequestStatus.REJECTED],
    RequestStatus.IN_PROGRESS: [RequestStatus.RESOLVED, RequestStatus.IN_REVIEW, RequestStatus.REJECTED],
    RequestStatus.RESOLVED: [RequestStatus.IN_PROGRESS],
    RequestStatus.REJECTED: [RequestStatus.SUBMITTED, RequestStatus.IN_REVIEW, RequestStatus.IN_PROGRESS],
}

PRIORITY_SORT_ORDER: dict[RequestPriority, int] = {
    RequestPriority.LOW: 1,
    RequestPriority.MEDIUM: 2,
    RequestPriority.HIGH: 3,
    RequestPriority.URGENT: 4,
}

DEFAULT_PRIORITY: dict[str, RequestPriority] = {
    RequestType.INCIDENT.value: RequestPriority.HIGH,
    RequestType.NEW_EQUIPMENT.value: RequestPriority.LOW,
    RequestType.ONBOARDING.value: RequestPriority.MEDIUM,
    RequestType.REPAIR.value: RequestPriority.MEDIUM,
    RequestType.CONFIGURATION.value: RequestPriority.LOW,
    RequestType.ACCESS_REQUEST.value: RequestPriority.LOW,
}


class InvalidStatusTransitionError(Exception):
    def __init__(self, current: RequestStatus, target: RequestStatus):
        self.current = current
        self.target = target
        super().__init__(f"Cannot transition from {current.value} to {target.value}")
