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


class AuthMode(str, Enum):
    """Authentication mode for a company."""
    DOMAIN = "domain"
    MEMBERSHIP_ONLY = "membership_only"


class CompanySector(str, Enum):
    FINANCIAL_SERVICES = "financial_services"
    HEALTHCARE = "healthcare"
    GOVERNMENT = "government"
    EDUCATION = "education"
    TECHNOLOGY = "technology"
    MANUFACTURING = "manufacturing"
    RETAIL = "retail"
    ENERGY = "energy"
    TELECOMMUNICATIONS = "telecommunications"
    PROFESSIONAL_SERVICES = "professional_services"
    LOGISTICS = "logistics"
    OTHER = "other"
