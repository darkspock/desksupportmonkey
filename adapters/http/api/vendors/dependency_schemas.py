from typing import Optional

from pydantic import BaseModel, Field


class CreateDependencyRequest(BaseModel):
    service_description: str = Field(min_length=1, max_length=500)
    business_function: str = Field(
        pattern="^(it_operations|security|communications|data_storage|cloud_infrastructure|software|hardware_supply|consulting|other)$",
    )
    is_critical: bool = False
    notes: Optional[str] = None


class UpdateDependencyRequest(BaseModel):
    service_description: Optional[str] = Field(
        default=None, min_length=1, max_length=500,
    )
    business_function: Optional[str] = Field(
        default=None,
        pattern="^(it_operations|security|communications|data_storage|cloud_infrastructure|software|hardware_supply|consulting|other)$",
    )
    is_critical: Optional[bool] = None
    notes: Optional[str] = None


class DependencyResponse(BaseModel):
    id: str
    vendor_id: str
    company_id: str
    service_description: str
    business_function: str
    is_critical: bool
    notes: Optional[str] = None
    created_at: Optional[str] = None


class ConcentrationRiskItemResponse(BaseModel):
    vendor_id: str
    vendor_name: str
    critical_count: int
    total_critical: int
    percentage: float
    is_above_threshold: bool
