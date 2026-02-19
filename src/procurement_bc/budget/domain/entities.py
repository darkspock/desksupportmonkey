from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import ulid


@dataclass
class DepartmentBudget:
    id: str
    company_id: str
    department_id: str
    fiscal_year: int
    allocated_amount_cents: int
    currency: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        company_id: str,
        department_id: str,
        fiscal_year: int,
        allocated_amount_cents: int,
        currency: str = "USD",
        id: Optional[str] = None,
    ) -> "DepartmentBudget":
        if allocated_amount_cents < 0:
            raise ValueError(
                "Budget amount cannot be negative"
            )
        return cls(
            id=id or str(ulid.new()),
            company_id=company_id,
            department_id=department_id,
            fiscal_year=fiscal_year,
            allocated_amount_cents=allocated_amount_cents,
            currency=currency,
        )


@dataclass
class CompanyProcurementConfig:
    id: str
    company_id: str
    enforcement_mode: str = "warn"
    approval_threshold_cents: int = 0
    po_number_prefix: str = "PO"
    fiscal_year_start_month: int = 1
    currency: str = "USD"
    auto_create_assets: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        company_id: str,
        enforcement_mode: str = "warn",
        approval_threshold_cents: int = 0,
        po_number_prefix: str = "PO",
        fiscal_year_start_month: int = 1,
        currency: str = "USD",
        auto_create_assets: bool = False,
        id: Optional[str] = None,
    ) -> "CompanyProcurementConfig":
        if enforcement_mode not in ("warn", "strict"):
            raise ValueError(
                f"Invalid enforcement mode: {enforcement_mode}"
            )
        if approval_threshold_cents < 0:
            raise ValueError(
                "Approval threshold cannot be negative"
            )
        if not 1 <= fiscal_year_start_month <= 12:
            raise ValueError(
                "Fiscal year start month must be 1-12"
            )
        return cls(
            id=id or str(ulid.new()),
            company_id=company_id,
            enforcement_mode=enforcement_mode,
            approval_threshold_cents=approval_threshold_cents,
            po_number_prefix=po_number_prefix,
            fiscal_year_start_month=fiscal_year_start_month,
            currency=currency,
            auto_create_assets=auto_create_assets,
        )

    @classmethod
    def defaults(cls, company_id: str) -> "CompanyProcurementConfig":
        return cls(
            id="",
            company_id=company_id,
        )
