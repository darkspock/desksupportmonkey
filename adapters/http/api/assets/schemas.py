from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class CreateAssetRequest(BaseModel):
    type: str
    brand: str = Field(min_length=1, max_length=255)
    model: str = Field(min_length=1, max_length=255)
    serial_number: str = Field(min_length=1, max_length=255)
    purchase_date: Optional[date] = None
    warranty_expiration: Optional[date] = None
    notes: Optional[str] = None
    custom_fields_data: Optional[dict[str, Any]] = None


class UpdateAssetRequest(BaseModel):
    type: Optional[str] = Field(None, min_length=1, max_length=100)
    brand: Optional[str] = Field(None, min_length=1, max_length=255)
    model: Optional[str] = Field(None, min_length=1, max_length=255)
    purchase_date: Optional[date] = None
    warranty_expiration: Optional[date] = None
    notes: Optional[str] = None
    custom_fields_data: Optional[dict[str, Any]] = None


class AssignAssetRequest(BaseModel):
    user_id: str = Field(min_length=1)


class ChangeStatusRequest(BaseModel):
    status: str


class AssetResponse(BaseModel):
    id: str
    company_id: str
    type: str
    brand: str
    model: str
    serial_number: str
    status: str
    assigned_to: Optional[str] = None
    assigned_to_email: Optional[str] = None
    department_id: Optional[str] = None
    location_id: Optional[str] = None
    location_name: Optional[str] = None
    purchase_date: Optional[date] = None
    warranty_expiration: Optional[date] = None
    notes: Optional[str] = None
    custom_fields: Optional[list[dict[str, Any]]] = None
    criticality: Optional[str] = None
    impact_score: Optional[int] = None
    rto_minutes: Optional[int] = None
    rpo_minutes: Optional[int] = None
    bia_justification: Optional[str] = None
    bia_reviewed_at: Optional[datetime] = None
    bia_reviewed_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class AssetEventResponse(BaseModel):
    id: str
    asset_id: str
    event_type: str
    data: dict
    performed_by: str
    performed_by_email: Optional[str] = None
    created_at: Optional[datetime] = None


class AssignableUserResponse(BaseModel):
    id: str
    email: str
    name: Optional[str] = None


class ImportRowErrorResponse(BaseModel):
    row: int
    error: str


class ImportResponse(BaseModel):
    total: int
    successful: int
    failed: list[ImportRowErrorResponse]


class CreateLocationRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    in_use: bool = True
    street_line_1: Optional[str] = Field(None, max_length=255)
    street_line_2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=50)


class UpdateLocationRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    in_use: Optional[bool] = None
    street_line_1: Optional[str] = Field(None, max_length=255)
    street_line_2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=50)


class AssetLocationResponse(BaseModel):
    id: str
    name: str
    is_system: bool
    system_key: Optional[str] = None
    in_use: bool
    street_line_1: Optional[str] = None
    street_line_2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    phone: Optional[str] = None
    is_personal: bool = False
    user_id: Optional[str] = None
    asset_count: int = 0
    created_at: Optional[datetime] = None


class CreateCIRelationshipRequest(BaseModel):
    target_asset_id: str = Field(..., min_length=1, max_length=26)
    relationship_type: str = Field(...)
    description: Optional[str] = Field(None, max_length=500)


class UpdateCIRelationshipRequest(BaseModel):
    description: Optional[str] = Field(None, max_length=500)


class CIRelationshipResponse(BaseModel):
    id: str
    source_asset_id: str
    target_asset_id: str
    relationship_type: str
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    created_by: str
    target_asset_name: Optional[str] = None
    target_asset_serial: Optional[str] = None
    target_asset_type: Optional[str] = None
    target_asset_criticality: Optional[str] = None
    target_asset_status: Optional[str] = None
    source_asset_name: Optional[str] = None
    source_asset_serial: Optional[str] = None
    source_asset_type: Optional[str] = None
    source_asset_criticality: Optional[str] = None
    source_asset_status: Optional[str] = None


class ImpactAssetResponse(BaseModel):
    id: str
    name: str
    asset_tag: Optional[str] = None
    criticality: Optional[str] = None
    depth: int
    relationship_type: str


class ImpactRadiusResponse(BaseModel):
    critical: int
    high: int
    medium: int
    low: int
    unclassified: int
    total: int


class AssetImpactResponse(BaseModel):
    asset_id: str
    upstream: list[ImpactAssetResponse]
    downstream: list[ImpactAssetResponse]
    radius: ImpactRadiusResponse


class MostDependedAssetResponse(BaseModel):
    asset_id: str
    asset_name: str
    asset_tag: Optional[str] = None
    incoming_count: int


class OverdueBIAReviewResponse(BaseModel):
    asset_id: str
    asset_name: str
    asset_tag: Optional[str] = None
    criticality: str
    bia_reviewed_at: Optional[datetime] = None


class CMDBDashboardResponse(BaseModel):
    criticality_distribution: dict[str, int]
    orphan_critical_count: int
    bia_total_critical_high: int
    bia_has_coverage: int
    bia_coverage_pct: float
    total_relationships: int
    relationships_by_type: dict[str, int]
    most_depended_upon: list[MostDependedAssetResponse]
    overdue_bia_reviews: list[OverdueBIAReviewResponse]


class MoveAssetRequest(BaseModel):
    location_id: str = Field(min_length=1)
    notes: Optional[str] = None


class SetCriticalityRequest(BaseModel):
    criticality: Optional[str] = None


class UpdateBiaRequest(BaseModel):
    impact_score: Optional[int] = Field(None, ge=1, le=10)
    rto_minutes: Optional[int] = Field(None, gt=0)
    rpo_minutes: Optional[int] = Field(None, ge=0)
    bia_justification: Optional[str] = None
