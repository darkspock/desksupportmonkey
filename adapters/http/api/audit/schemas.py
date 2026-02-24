from datetime import datetime
from typing import Optional

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class ExportAuditRequest(BaseModel):
    format: str = "csv"  # "csv" or "pdf"
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    actor_id: Optional[str] = None
    action: Optional[str] = None
    resource_type: Optional[str] = None
    control_id: Optional[str] = None


class AddAuditTagsRequest(BaseModel):
    control_ids: list[str]


class CreateControlRequest(BaseModel):
    code: str
    name: str
    framework: str
    description: Optional[str] = None


class UpdateControlRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class AuditEntryListResponse(BaseModel):
    id: str
    actor_email: str
    actor_name: Optional[str] = None
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    http_method: str
    response_status: int
    ip_address: Optional[str] = None
    created_at: Optional[datetime] = None
    tag_count: int = 0


class AuditTagResponse(BaseModel):
    id: str
    control_id: str
    control_code: str
    control_name: str
    framework: str
    tagged_by: str
    tagged_at: Optional[datetime] = None


class AuditEntryDetailResponse(BaseModel):
    id: str
    company_id: Optional[str] = None
    actor_id: Optional[str] = None
    actor_email: str
    actor_name: Optional[str] = None
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    http_method: str
    http_path: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_data: Optional[dict] = None
    response_status: int
    changes: Optional[dict] = None
    hash: str
    created_at: Optional[datetime] = None
    tags: list[AuditTagResponse] = []


class ComplianceControlResponse(BaseModel):
    id: str
    code: str
    name: str
    framework: str
    description: Optional[str] = None
    is_predefined: bool
    is_active: bool
    created_at: Optional[datetime] = None


class ExportStatusResponse(BaseModel):
    task_id: str
    status: str
    download_url: Optional[str] = None


# ---------------------------------------------------------------------------
# GDPR schemas
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Retention & Integrity schemas
# ---------------------------------------------------------------------------


class UpdateRetentionRequest(BaseModel):
    retention_months: int


class RetentionPolicyResponse(BaseModel):
    retention_months: int
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] = None


class VerifyIntegrityRequest(BaseModel):
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


class VerifyIntegrityResponse(BaseModel):
    task_id: str
    status: str
    total_checked: Optional[int] = None
    valid_count: Optional[int] = None
    invalid_count: Optional[int] = None
    first_invalid_entry_id: Optional[str] = None


# ---------------------------------------------------------------------------
# GDPR schemas
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Compliance assessment & evidence schemas
# ---------------------------------------------------------------------------


class AssessControlRequest(BaseModel):
    status: str
    notes: Optional[str] = None


class AddEvidenceRequest(BaseModel):
    evidence_type: str
    title: str
    reference_id: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None


class ExportComplianceRequest(BaseModel):
    framework: Optional[str] = None


class ControlAssessmentResponse(BaseModel):
    control_id: str
    control_code: str
    control_name: str
    framework: str
    description: Optional[str] = None
    is_predefined: bool
    status: str
    notes: Optional[str] = None
    assessed_by: Optional[str] = None
    assessed_at: Optional[datetime] = None
    evidence_count: int = 0


class ComplianceEvidenceResponse(BaseModel):
    id: str
    control_id: str
    evidence_type: str
    reference_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    url: Optional[str] = None
    added_by: str
    created_at: Optional[datetime] = None


class FrameworkSummaryResponse(BaseModel):
    framework: str
    total_controls: int
    compliant: int
    partial: int
    non_compliant: int
    not_assessed: int
    compliance_pct: float
    evidence_coverage_pct: float


class ComplianceDashboardResponse(BaseModel):
    overall_compliance_pct: float
    total_controls: int
    compliant: int
    partial: int
    non_compliant: int
    not_assessed: int
    controls_with_evidence: int
    controls_without_evidence: int
    frameworks: list[FrameworkSummaryResponse] = []
    gap_controls: list[ControlAssessmentResponse] = []


class GdprExportRequest(BaseModel):
    target_user_email: str


class GdprAnonymizeRequest(BaseModel):
    target_user_email: str
    reason: str


class GdprRequestListResponse(BaseModel):
    id: str
    target_user_email: str
    request_type: str
    status: str
    reason: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


class GdprRequestDetailResponse(BaseModel):
    id: str
    target_user_email: str
    request_type: str
    status: str
    reason: Optional[str] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    download_url: Optional[str] = None
