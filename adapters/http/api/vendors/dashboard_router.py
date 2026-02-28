import logging

from fastapi import APIRouter, Depends, HTTPException, status

from adapters.http.api.auth.dependencies import get_current_user
from adapters.http.api.vendors.dashboard_schemas import (
    ConcentrationRiskItemResponse,
    ExpiringContractResponse,
    ExportVendorRiskRequest,
    ExportVendorRiskResponse,
    SupplyChainDashboardResponse,
)
from adapters.http.api.vendors.dependencies import get_vendor_repo
from adapters.http.api.vendors.contract_dependencies import get_contract_repo
from adapters.http.api.vendors.assessment_dependencies import get_assessment_repo
from adapters.http.api.vendors.dependency_dependencies import get_dependency_repo
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
from src.procurement_bc.vendor.application.queries.supply_chain_dashboard import (
    SupplyChainDashboardQuery,
    SupplyChainDashboardQueryHandler,
)
from src.procurement_bc.vendor.domain.repository import (
    VendorContractRepositoryInterface,
    VendorDependencyRepositoryInterface,
    VendorRepositoryInterface,
    VendorRiskAssessmentRepositoryInterface,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/vendors",
    tags=["vendors-dashboard"],
)


@router.get(
    "/supply-chain-dashboard",
    response_model=SupplyChainDashboardResponse,
)
def get_supply_chain_dashboard(
    current_user: User = Depends(get_current_user),
    vendor_repo: VendorRepositoryInterface = Depends(get_vendor_repo),
    contract_repo: VendorContractRepositoryInterface = Depends(get_contract_repo),
    assessment_repo: VendorRiskAssessmentRepositoryInterface = Depends(get_assessment_repo),
    dependency_repo: VendorDependencyRepositoryInterface = Depends(get_dependency_repo),
) -> SupplyChainDashboardResponse:
    if current_user.role not in (
        UserRole.TECHNICIAN,
        UserRole.ADMIN,
        UserRole.SUPER_ADMIN,
        UserRole.PROCUREMENT_MANAGER,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    handler = SupplyChainDashboardQueryHandler(
        vendor_repo=vendor_repo,
        contract_repo=contract_repo,
        assessment_repo=assessment_repo,
        dependency_repo=dependency_repo,
    )
    dto = handler.handle(
        SupplyChainDashboardQuery(company_id=current_user.company_id),
    )

    return SupplyChainDashboardResponse(
        total_vendors=dto.total_vendors,
        active_vendors=dto.active_vendors,
        vendors_by_risk_level=dto.vendors_by_risk_level,
        critical_ict_count=dto.critical_ict_count,
        expiring_contracts_30=dto.expiring_contracts_30,
        expiring_contracts_60=dto.expiring_contracts_60,
        expiring_contracts_90=dto.expiring_contracts_90,
        expiring_contracts=[
            ExpiringContractResponse(
                contract_id=c.contract_id,
                vendor_id=c.vendor_id,
                vendor_name=c.vendor_name,
                title=c.title,
                end_date=c.end_date,
                days_remaining=c.days_remaining,
            )
            for c in dto.expiring_contracts
        ],
        concentration_risk_items=[
            ConcentrationRiskItemResponse(
                vendor_id=i.vendor_id,
                vendor_name=i.vendor_name,
                critical_count=i.critical_count,
                total_critical=i.total_critical,
                percentage=i.percentage,
                is_above_threshold=i.is_above_threshold,
            )
            for i in dto.concentration_risk_items
        ],
        stale_assessment_count=dto.stale_assessment_count,
    )


@router.post(
    "/risk-export",
    response_model=ExportVendorRiskResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def export_vendor_risk(
    body: ExportVendorRiskRequest,
    current_user: User = Depends(get_current_user),
) -> ExportVendorRiskResponse:
    if current_user.role not in (
        UserRole.ADMIN,
        UserRole.SUPER_ADMIN,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    from core.tasks.vendor_contracts import export_vendor_risk_report

    result = export_vendor_risk_report.delay(
        company_id=current_user.company_id,
        requested_by=current_user.id,
        export_format=body.format,
    )

    return ExportVendorRiskResponse(
        download_url="",
        storage_key=f"vendor-risk-exports/{current_user.company_id}/{result.id}.{body.format}",
        format=body.format,
    )
