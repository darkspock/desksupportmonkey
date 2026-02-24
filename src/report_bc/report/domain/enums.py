from enum import Enum


class ReportType(str, Enum):
    ASSET_INVENTORY = "asset_inventory"
    REQUEST_SUMMARY = "request_summary"
    TECHNICIAN_PERFORMANCE = "technician_performance"
    DEPARTMENT_SPENDING = "department_spending"
    SLA_COMPLIANCE = "sla_compliance"


class ReportStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
