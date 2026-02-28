from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


# --- Requests ---


class CreateVulnerabilityRequest(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    cve_id: Optional[str] = None
    description: Optional[str] = None
    cvss_score: Optional[float] = Field(None, ge=0.0, le=10.0)
    severity: Optional[str] = None
    affected_software: Optional[str] = None
    affected_versions: Optional[str] = None
    published_at: Optional[date] = None
    discovered_at: Optional[date] = None
    remediation_notes: Optional[str] = None
    vendor_id: Optional[str] = None


class UpdateVulnerabilityRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    cvss_score: Optional[float] = Field(None, ge=0.0, le=10.0)
    affected_software: Optional[str] = None
    affected_versions: Optional[str] = None
    remediation_notes: Optional[str] = None


class ChangeVulnerabilityStatusRequest(BaseModel):
    status: str
    justification: Optional[str] = None


class LinkAssetsRequest(BaseModel):
    asset_ids: list[str] = Field(min_length=1)
    notes: Optional[str] = None


class UpdateRemediationStatusRequest(BaseModel):
    status: str
    notes: Optional[str] = None


# --- Responses ---


class VulnerabilityListItemResponse(BaseModel):
    id: str
    cve_id: Optional[str] = None
    title: str
    source: str
    cvss_score: Optional[float] = None
    severity: str
    status: str
    affected_software: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class VulnerabilityEventResponse(BaseModel):
    id: str
    event_type: str
    data: Optional[dict] = None
    performed_by: str
    performed_by_name: Optional[str] = None
    created_at: Optional[datetime] = None


class LinkAssetsResponse(BaseModel):
    linked: int
    skipped: int
    errors: list[dict] = []


class VulnerabilityAssetResponse(BaseModel):
    id: str
    asset_id: str
    asset_name: Optional[str] = None
    asset_tag: Optional[str] = None
    asset_criticality: Optional[str] = None
    status: str
    notes: Optional[str] = None
    remediation_request_id: Optional[str] = None
    patched_at: Optional[datetime] = None
    patched_by: Optional[str] = None
    patched_by_name: Optional[str] = None
    created_at: Optional[datetime] = None


class ImportRowErrorResponse(BaseModel):
    row: int
    error: str


class ImportResponse(BaseModel):
    total: int
    successful: int
    skipped: int
    failed: list[ImportRowErrorResponse]


class TicketCreatedResponse(BaseModel):
    asset_id: str
    request_id: str


class CreateTicketsResponse(BaseModel):
    created: list[TicketCreatedResponse]
    skipped: int
    errors: list[dict] = []


class VulnerabilityDetailResponse(BaseModel):
    id: str
    cve_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    source: str
    cvss_score: Optional[float] = None
    severity: str
    status: str
    affected_software: Optional[str] = None
    affected_versions: Optional[str] = None
    published_at: Optional[date] = None
    discovered_at: Optional[date] = None
    remediation_notes: Optional[str] = None
    vendor_id: Optional[str] = None
    created_by: str
    created_by_name: Optional[str] = None
    events: list[VulnerabilityEventResponse] = []
    affected_assets: list[VulnerabilityAssetResponse] = []
    all_assets_remediated: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
