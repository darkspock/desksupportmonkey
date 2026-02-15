from enum import Enum


class CompanyStatus(str, Enum):
    """Company lifecycle statuses."""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    DEACTIVATED = "deactivated"


VALID_TRANSITIONS: dict[CompanyStatus, list[CompanyStatus]] = {
    CompanyStatus.ACTIVE: [CompanyStatus.SUSPENDED, CompanyStatus.DEACTIVATED],
    CompanyStatus.SUSPENDED: [CompanyStatus.ACTIVE, CompanyStatus.DEACTIVATED],
    CompanyStatus.DEACTIVATED: [],  # terminal state
}
