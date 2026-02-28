from enum import Enum


class ContractType(str, Enum):
    SERVICE = "service"
    SUPPLY = "supply"
    LICENSING = "licensing"
    SAAS = "saas"


class ContractStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    EXPIRED = "expired"
    TERMINATED = "terminated"


VALID_CONTRACT_TRANSITIONS: dict[ContractStatus, list[ContractStatus]] = {
    ContractStatus.DRAFT: [ContractStatus.ACTIVE, ContractStatus.TERMINATED],
    ContractStatus.ACTIVE: [ContractStatus.EXPIRED, ContractStatus.TERMINATED],
    ContractStatus.EXPIRED: [ContractStatus.ACTIVE],
    ContractStatus.TERMINATED: [ContractStatus.DRAFT],
}


class VendorCategory(str, Enum):
    HARDWARE = "hardware"
    SOFTWARE = "software"
    SAAS = "saas"
    CONSULTING = "consulting"
    TELECOM = "telecom"
    CLOUD = "cloud"
    MANAGED_SERVICES = "managed_services"
    OTHER = "other"


class VendorRiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class BusinessFunction(str, Enum):
    IT_OPERATIONS = "it_operations"
    SECURITY = "security"
    COMMUNICATIONS = "communications"
    DATA_STORAGE = "data_storage"
    CLOUD_INFRASTRUCTURE = "cloud_infrastructure"
    SOFTWARE = "software"
    HARDWARE_SUPPLY = "hardware_supply"
    CONSULTING = "consulting"
    OTHER = "other"


DEFAULT_SECURITY_CLAUSES: dict[str, bool] = {
    "data_processing_agreement": False,
    "breach_notification_clause": False,
    "audit_rights": False,
    "exit_strategy": False,
    "subcontractor_oversight": False,
    "data_location_restrictions": False,
    "business_continuity_plan": False,
}
