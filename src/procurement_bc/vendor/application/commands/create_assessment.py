import logging
from dataclasses import dataclass
from datetime import date
from typing import Optional

from src.framework.application.command_bus import (
    Command,
    CommandHandler,
)
from src.procurement_bc.vendor.domain.entities import (
    VendorRiskAssessment,
    calculate_vendor_risk_level,
)
from src.procurement_bc.vendor.domain.exceptions import VendorNotFoundError
from src.procurement_bc.vendor.domain.repository import (
    VendorContractRepositoryInterface,
    VendorRiskAssessmentRepositoryInterface,
    VendorRepositoryInterface,
)

logger = logging.getLogger(__name__)


@dataclass
class CreateAssessmentCommand(Command):
    vendor_id: str
    company_id: str
    assessed_by: str
    assessment_date: date
    data_handling_score: int
    security_certs_score: int
    incident_response_score: int
    business_continuity_score: int
    subcontractor_score: int
    next_review_date: Optional[date] = None
    justification: Optional[str] = None
    id: str = ""
    performed_by: str = ""


class CreateAssessmentCommandHandler(
    CommandHandler[CreateAssessmentCommand],
):
    def __init__(
        self,
        vendor_repo: VendorRepositoryInterface,
        assessment_repo: VendorRiskAssessmentRepositoryInterface,
        contract_repo: VendorContractRepositoryInterface,
    ):
        self.vendor_repo = vendor_repo
        self.assessment_repo = assessment_repo
        self.contract_repo = contract_repo

    def handle(self, command: CreateAssessmentCommand) -> None:
        vendor = self.vendor_repo.find_by_id(
            command.vendor_id, command.company_id,
        )
        if not vendor:
            raise VendorNotFoundError("Vendor not found")

        assessment = VendorRiskAssessment.create(
            id=command.id or None,
            vendor_id=command.vendor_id,
            company_id=command.company_id,
            assessed_by=command.assessed_by,
            assessment_date=command.assessment_date,
            data_handling_score=command.data_handling_score,
            security_certs_score=command.security_certs_score,
            incident_response_score=command.incident_response_score,
            business_continuity_score=command.business_continuity_score,
            subcontractor_score=command.subcontractor_score,
            next_review_date=command.next_review_date,
            justification=command.justification,
        )
        self.assessment_repo.save(assessment)

        has_clauses = self.contract_repo.has_active_contract_with_security_clauses(
            command.vendor_id, command.company_id,
        )
        vendor.risk_level = calculate_vendor_risk_level(
            assessment.overall_risk_level,
            vendor.is_critical_ict,
            has_clauses,
        )
        self.vendor_repo.save(vendor)

        logger.info(
            "Assessment %s created for vendor %s (risk_level=%s)",
            assessment.id,
            command.vendor_id,
            vendor.risk_level.value,
        )
