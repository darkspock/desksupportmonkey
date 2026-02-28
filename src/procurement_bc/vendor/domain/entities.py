from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

import ulid

from src.procurement_bc.vendor.domain.enums import (
    BusinessFunction,
    ContractStatus,
    ContractType,
    VendorCategory,
    VendorRiskLevel,
    VALID_CONTRACT_TRANSITIONS,
)
from src.procurement_bc.vendor.domain.exceptions import (
    InvalidContractTransitionError,
    InvalidAssessmentScoreError,
)


@dataclass
class Vendor:
    id: str
    company_id: str
    name: str
    is_active: bool = True
    contact_email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    is_critical_ict: bool = False
    risk_level: Optional[VendorRiskLevel] = None
    website: Optional[str] = None
    category: Optional[VendorCategory] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        company_id: str,
        name: str,
        contact_email: Optional[str] = None,
        phone: Optional[str] = None,
        address: Optional[str] = None,
        notes: Optional[str] = None,
        id: Optional[str] = None,
    ) -> "Vendor":
        if not name or not name.strip():
            raise ValueError("Vendor name is required")
        return cls(
            id=id or str(ulid.new()),
            company_id=company_id,
            name=name.strip(),
            is_active=True,
            contact_email=contact_email,
            phone=phone,
            address=address,
            notes=notes,
        )

    def activate(self) -> None:
        self.is_active = True

    def deactivate(self) -> None:
        self.is_active = False

    def update_extended_fields(
        self,
        category: Optional[VendorCategory] = None,
        website: Optional[str] = None,
        is_critical_ict: Optional[bool] = None,
    ) -> None:
        if category is not None:
            self.category = category
        if website is not None:
            self.website = website
        if is_critical_ict is not None:
            self.is_critical_ict = is_critical_ict


@dataclass
class VendorContract:
    id: str
    vendor_id: str
    company_id: str
    contract_type: ContractType
    title: str
    start_date: date
    status: ContractStatus
    end_date: Optional[date] = None
    renewal_date: Optional[date] = None
    auto_renewal: bool = False
    annual_value: Optional[Decimal] = None
    currency: Optional[str] = None
    security_clauses: dict = field(default_factory=dict)
    notes: Optional[str] = None
    is_deleted: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        vendor_id: str,
        company_id: str,
        contract_type: ContractType,
        title: str,
        start_date: date,
        end_date: Optional[date] = None,
        renewal_date: Optional[date] = None,
        auto_renewal: bool = False,
        annual_value: Optional[Decimal] = None,
        currency: Optional[str] = None,
        security_clauses: Optional[dict] = None,
        notes: Optional[str] = None,
        id: Optional[str] = None,
    ) -> "VendorContract":
        if not title or not title.strip():
            raise ValueError("Contract title is required")
        return cls(
            id=id or str(ulid.new()),
            vendor_id=vendor_id,
            company_id=company_id,
            contract_type=contract_type,
            title=title.strip(),
            start_date=start_date,
            status=ContractStatus.DRAFT,
            end_date=end_date,
            renewal_date=renewal_date,
            auto_renewal=auto_renewal,
            annual_value=annual_value,
            currency=currency,
            security_clauses=security_clauses or {},
            notes=notes,
        )

    def change_status(self, new_status: ContractStatus) -> None:
        allowed = VALID_CONTRACT_TRANSITIONS.get(self.status, [])
        if new_status not in allowed:
            raise InvalidContractTransitionError(
                f"Cannot transition from {self.status.value} to {new_status.value}"
            )
        self.status = new_status

    def update(
        self,
        title: Optional[str] = None,
        contract_type: Optional[ContractType] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        renewal_date: Optional[date] = None,
        auto_renewal: Optional[bool] = None,
        annual_value: Optional[Decimal] = None,
        currency: Optional[str] = None,
        security_clauses: Optional[dict] = None,
        notes: Optional[str] = None,
    ) -> None:
        if title is not None:
            if not title.strip():
                raise ValueError("Contract title is required")
            self.title = title.strip()
        if contract_type is not None:
            self.contract_type = contract_type
        if start_date is not None:
            self.start_date = start_date
        if end_date is not None:
            self.end_date = end_date
        if renewal_date is not None:
            self.renewal_date = renewal_date
        if auto_renewal is not None:
            self.auto_renewal = auto_renewal
        if annual_value is not None:
            self.annual_value = annual_value
        if currency is not None:
            self.currency = currency
        if security_clauses is not None:
            self.security_clauses = security_clauses
        if notes is not None:
            self.notes = notes

    def soft_delete(self) -> None:
        self.is_deleted = True


@dataclass
class VendorContractDocument:
    id: str
    contract_id: str
    company_id: str
    filename: str
    content_type: str
    size_bytes: int
    storage_key: str
    uploaded_by: str
    is_deleted: bool = False
    created_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        contract_id: str,
        company_id: str,
        filename: str,
        content_type: str,
        size_bytes: int,
        storage_key: str,
        uploaded_by: str,
        id: Optional[str] = None,
    ) -> "VendorContractDocument":
        if not filename or not filename.strip():
            raise ValueError("Filename is required")
        return cls(
            id=id or str(ulid.new()),
            contract_id=contract_id,
            company_id=company_id,
            filename=filename.strip(),
            content_type=content_type,
            size_bytes=size_bytes,
            storage_key=storage_key,
            uploaded_by=uploaded_by,
        )

    def soft_delete(self) -> None:
        self.is_deleted = True


@dataclass
class VendorRiskAssessment:
    id: str
    vendor_id: str
    company_id: str
    assessed_by: str
    assessment_date: date
    data_handling_score: int
    security_certs_score: int
    incident_response_score: int
    business_continuity_score: int
    subcontractor_score: int
    overall_risk_level: VendorRiskLevel
    next_review_date: Optional[date] = None
    justification: Optional[str] = None
    is_deleted: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        vendor_id: str,
        company_id: str,
        assessed_by: str,
        assessment_date: date,
        data_handling_score: int,
        security_certs_score: int,
        incident_response_score: int,
        business_continuity_score: int,
        subcontractor_score: int,
        next_review_date: Optional[date] = None,
        justification: Optional[str] = None,
        id: Optional[str] = None,
    ) -> "VendorRiskAssessment":
        scores = [
            data_handling_score,
            security_certs_score,
            incident_response_score,
            business_continuity_score,
            subcontractor_score,
        ]
        for score in scores:
            if not isinstance(score, int) or score < 1 or score > 5:
                raise InvalidAssessmentScoreError(
                    f"All scores must be integers between 1 and 5, got {score}"
                )
        risk_level = cls.calculate_risk_level(scores)
        return cls(
            id=id or str(ulid.new()),
            vendor_id=vendor_id,
            company_id=company_id,
            assessed_by=assessed_by,
            assessment_date=assessment_date,
            data_handling_score=data_handling_score,
            security_certs_score=security_certs_score,
            incident_response_score=incident_response_score,
            business_continuity_score=business_continuity_score,
            subcontractor_score=subcontractor_score,
            overall_risk_level=risk_level,
            next_review_date=next_review_date,
            justification=justification,
        )

    @classmethod
    def calculate_risk_level(cls, scores: list[int]) -> VendorRiskLevel:
        avg = sum(scores) / len(scores)
        if avg <= 2.0:
            return VendorRiskLevel.LOW
        elif avg <= 3.0:
            return VendorRiskLevel.MEDIUM
        elif avg <= 4.0:
            return VendorRiskLevel.HIGH
        else:
            return VendorRiskLevel.CRITICAL

    def soft_delete(self) -> None:
        self.is_deleted = True


def calculate_vendor_risk_level(
    assessment_level: VendorRiskLevel,
    is_critical_ict: bool,
    has_security_clauses: bool,
) -> VendorRiskLevel:
    if is_critical_ict and not has_security_clauses:
        return VendorRiskLevel.CRITICAL
    return assessment_level


@dataclass
class VendorDependency:
    id: str
    vendor_id: str
    company_id: str
    service_description: str
    business_function: BusinessFunction
    is_critical: bool
    notes: Optional[str] = None
    is_deleted: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        vendor_id: str,
        company_id: str,
        service_description: str,
        business_function: BusinessFunction,
        is_critical: bool = False,
        notes: Optional[str] = None,
        id: Optional[str] = None,
    ) -> "VendorDependency":
        if not service_description or not service_description.strip():
            raise ValueError("Service description is required")
        return cls(
            id=id or str(ulid.new()),
            vendor_id=vendor_id,
            company_id=company_id,
            service_description=service_description.strip(),
            business_function=business_function,
            is_critical=is_critical,
            notes=notes,
        )

    def update(
        self,
        service_description: Optional[str] = None,
        business_function: Optional[BusinessFunction] = None,
        is_critical: Optional[bool] = None,
        notes: Optional[str] = None,
    ) -> None:
        if service_description is not None:
            if not service_description.strip():
                raise ValueError("Service description is required")
            self.service_description = service_description.strip()
        if business_function is not None:
            self.business_function = business_function
        if is_critical is not None:
            self.is_critical = is_critical
        if notes is not None:
            self.notes = notes

    def soft_delete(self) -> None:
        self.is_deleted = True
