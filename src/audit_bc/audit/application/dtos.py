from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class AuditEntryDto:
    id: str
    actor_email: str
    actor_name: Optional[str]
    action: str
    resource_type: str
    resource_id: Optional[str]
    http_method: str
    response_status: int
    ip_address: Optional[str]
    created_at: Optional[datetime]
    tag_count: int


@dataclass
class AuditTagDto:
    id: str
    control_id: str
    control_code: str
    control_name: str
    framework: str
    tagged_by: str
    tagged_at: Optional[datetime]


@dataclass
class AuditEntryDetailDto:
    id: str
    company_id: Optional[str]
    actor_id: Optional[str]
    actor_email: str
    actor_name: Optional[str]
    action: str
    resource_type: str
    resource_id: Optional[str]
    http_method: str
    http_path: str
    ip_address: Optional[str]
    user_agent: Optional[str]
    request_data: Optional[dict]
    response_status: int
    changes: Optional[dict]
    hash: str
    created_at: Optional[datetime]
    tags: list[AuditTagDto]


@dataclass
class GdprRequestDto:
    id: str
    company_id: str
    target_user_id: str
    target_user_email: str
    requested_by: str
    request_type: str
    status: str
    reason: Optional[str]
    storage_key: Optional[str]
    error_message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: Optional[datetime]


@dataclass
class RetentionPolicyDto:
    retention_months: int
    updated_at: Optional[datetime]
    updated_by: Optional[str]


@dataclass
class ComplianceControlDto:
    id: str
    code: str
    name: str
    framework: str
    description: Optional[str]
    is_predefined: bool
    is_active: bool
    created_at: Optional[datetime]


@dataclass
class ControlAssessmentDto:
    control_id: str
    control_code: str
    control_name: str
    framework: str
    description: Optional[str]
    is_predefined: bool
    status: str
    notes: Optional[str]
    assessed_by: Optional[str]
    assessed_at: Optional[datetime]
    evidence_count: int


@dataclass
class ComplianceEvidenceDto:
    id: str
    control_id: str
    evidence_type: str
    reference_id: Optional[str]
    title: str
    description: Optional[str]
    url: Optional[str]
    added_by: str
    created_at: Optional[datetime]


@dataclass
class FrameworkSummaryDto:
    framework: str
    total_controls: int
    compliant: int
    partial: int
    non_compliant: int
    not_assessed: int
    compliance_pct: float
    evidence_coverage_pct: float


@dataclass
class ComplianceDashboardDto:
    overall_compliance_pct: float
    total_controls: int
    compliant: int
    partial: int
    non_compliant: int
    not_assessed: int
    controls_with_evidence: int
    controls_without_evidence: int
    frameworks: list[FrameworkSummaryDto]
    gap_controls: list[ControlAssessmentDto]
