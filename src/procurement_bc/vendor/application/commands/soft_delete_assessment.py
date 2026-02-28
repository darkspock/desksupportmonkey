import logging
from dataclasses import dataclass

from src.framework.application.command_bus import (
    Command,
    CommandHandler,
)
from src.procurement_bc.vendor.domain.entities import calculate_vendor_risk_level
from src.procurement_bc.vendor.domain.exceptions import (
    AssessmentNotFoundError,
    VendorNotFoundError,
)
from src.procurement_bc.vendor.domain.repository import (
    VendorContractRepositoryInterface,
    VendorRiskAssessmentRepositoryInterface,
    VendorRepositoryInterface,
)

logger = logging.getLogger(__name__)


@dataclass
class SoftDeleteAssessmentCommand(Command):
    assessment_id: str
    vendor_id: str
    company_id: str
    performed_by: str = ""


class SoftDeleteAssessmentCommandHandler(
    CommandHandler[SoftDeleteAssessmentCommand],
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

    def handle(self, command: SoftDeleteAssessmentCommand) -> None:
        assessment = self.assessment_repo.find_by_id(
            command.assessment_id,
            command.vendor_id,
            command.company_id,
        )
        if not assessment:
            raise AssessmentNotFoundError("Assessment not found")

        self.assessment_repo.soft_delete(
            command.assessment_id,
            command.vendor_id,
            command.company_id,
        )

        vendor = self.vendor_repo.find_by_id(
            command.vendor_id, command.company_id,
        )
        if not vendor:
            raise VendorNotFoundError("Vendor not found")

        latest = self.assessment_repo.find_latest_by_vendor(
            command.vendor_id, command.company_id,
        )
        if latest:
            has_clauses = self.contract_repo.has_active_contract_with_security_clauses(
                command.vendor_id, command.company_id,
            )
            vendor.risk_level = calculate_vendor_risk_level(
                latest.overall_risk_level,
                vendor.is_critical_ict,
                has_clauses,
            )
        else:
            vendor.risk_level = None
        self.vendor_repo.save(vendor)

        logger.info(
            "Assessment %s soft-deleted for vendor %s",
            command.assessment_id,
            command.vendor_id,
        )
