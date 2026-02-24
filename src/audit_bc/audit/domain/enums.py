from enum import Enum


class GdprRequestType(str, Enum):
    EXPORT = "export"
    ANONYMIZE = "anonymize"


class GdprRequestStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ComplianceStatus(str, Enum):
    COMPLIANT = "compliant"
    PARTIAL = "partial"
    NON_COMPLIANT = "non_compliant"
    NOT_ASSESSED = "not_assessed"


class EvidenceType(str, Enum):
    AUDIT_LOG = "audit_log"
    INCIDENT = "incident"
    RISK = "risk"
    SLA = "sla"
    MANUAL = "manual"
