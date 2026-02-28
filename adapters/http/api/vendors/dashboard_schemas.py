from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class ExpiringContractResponse(BaseModel):
    contract_id: str
    vendor_id: str
    vendor_name: str
    title: str
    end_date: date
    days_remaining: int


class ConcentrationRiskItemResponse(BaseModel):
    vendor_id: str
    vendor_name: str
    critical_count: int
    total_critical: int
    percentage: float
    is_above_threshold: bool


class SupplyChainDashboardResponse(BaseModel):
    total_vendors: int
    active_vendors: int
    vendors_by_risk_level: dict[str, int]
    critical_ict_count: int
    expiring_contracts_30: int
    expiring_contracts_60: int
    expiring_contracts_90: int
    expiring_contracts: list[ExpiringContractResponse]
    concentration_risk_items: list[ConcentrationRiskItemResponse]
    stale_assessment_count: int


class ExportVendorRiskRequest(BaseModel):
    format: str = Field(
        ..., pattern="^(pdf|csv)$",
        description="Export format: 'pdf' or 'csv'",
    )


class ExportVendorRiskResponse(BaseModel):
    download_url: str
    storage_key: str
    format: str
