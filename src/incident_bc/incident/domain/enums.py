from enum import Enum


class IncidentType(str, Enum):
    MALWARE = "malware"
    DATA_BREACH = "data_breach"
    DDOS = "ddos"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    PHISHING = "phishing"
    RANSOMWARE = "ransomware"
    OTHER = "other"


class IncidentSeverity(str, Enum):
    P1 = "P1"  # Critical
    P2 = "P2"  # High
    P3 = "P3"  # Medium
    P4 = "P4"  # Low


class IncidentStatus(str, Enum):
    DETECTED = "detected"
    TRIAGED = "triaged"
    CONTAINED = "contained"
    ERADICATED = "eradicated"
    RECOVERED = "recovered"
    CLOSED = "closed"


VALID_STATUS_TRANSITIONS: dict[IncidentStatus, list[IncidentStatus]] = {
    IncidentStatus.DETECTED: [IncidentStatus.TRIAGED, IncidentStatus.CLOSED],
    IncidentStatus.TRIAGED: [IncidentStatus.CONTAINED, IncidentStatus.CLOSED],
    IncidentStatus.CONTAINED: [IncidentStatus.ERADICATED, IncidentStatus.CLOSED],
    IncidentStatus.ERADICATED: [IncidentStatus.RECOVERED, IncidentStatus.CLOSED],
    IncidentStatus.RECOVERED: [IncidentStatus.CLOSED],
    IncidentStatus.CLOSED: [],
}


class TimelineEventType(str, Enum):
    INCIDENT_CREATED = "incident_created"
    INCIDENT_UPDATED = "incident_updated"
    STATUS_CHANGE = "status_change"
    SEVERITY_CHANGE = "severity_change"
    ASSIGNMENT = "assignment"
    COMMENT = "comment"
    ASSET_LINKED = "asset_linked"
    ASSET_UNLINKED = "asset_unlinked"
    VENDOR_LINKED = "vendor_linked"
    VENDOR_UNLINKED = "vendor_unlinked"
    REPORT_GENERATED = "report_generated"
    REPORT_REGENERATED = "report_regenerated"
    REPORT_SUBMITTED = "report_submitted"
    ESCALATION = "escalation"
    POSTMORTEM_CREATED = "postmortem_created"
    POSTMORTEM_UPDATED = "postmortem_updated"


class ReportType(str, Enum):
    EARLY_WARNING_24H = "early_warning_24h"
    DETAILED_72H = "detailed_72h"
    FINAL_30D = "final_30d"


class ReportStatus(str, Enum):
    PENDING = "pending"
    GENERATED = "generated"
    SUBMITTED = "submitted"
