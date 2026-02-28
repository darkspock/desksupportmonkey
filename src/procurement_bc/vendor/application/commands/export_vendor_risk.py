import csv
import io
import logging
import os
from dataclasses import dataclass, field
from datetime import date, datetime, timezone

from jinja2 import Environment, FileSystemLoader

from src.framework.application.command_bus import Command, CommandHandler
from src.procurement_bc.vendor.domain.enums import ContractStatus
from src.procurement_bc.vendor.domain.repository import (
    VendorContractRepositoryInterface,
    VendorDependencyRepositoryInterface,
    VendorRepositoryInterface,
    VendorRiskAssessmentRepositoryInterface,
)

logger = logging.getLogger(__name__)

TEMPLATE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))),
    "templates",
)


@dataclass
class ExportVendorRiskCommand(Command):
    company_id: str
    export_format: str  # "pdf" or "csv"
    requested_by: str
    task_id: str = ""


class ExportVendorRiskCommandHandler(
    CommandHandler[ExportVendorRiskCommand],
):
    def __init__(
        self,
        vendor_repo: VendorRepositoryInterface,
        contract_repo: VendorContractRepositoryInterface,
        assessment_repo: VendorRiskAssessmentRepositoryInterface,
        dependency_repo: VendorDependencyRepositoryInterface,
    ):
        self.vendor_repo = vendor_repo
        self.contract_repo = contract_repo
        self.assessment_repo = assessment_repo
        self.dependency_repo = dependency_repo

    def handle(self, command: ExportVendorRiskCommand) -> bytes:  # type: ignore[override]
        today = date.today()
        vendors, _ = self.vendor_repo.find_all(
            command.company_id, page=1, page_size=10000,
        )

        rows: list[dict] = []
        for v in vendors:
            latest = self.assessment_repo.find_latest_by_vendor(
                v.id, command.company_id,
            )
            contracts, contract_count = self.contract_repo.find_all_by_vendor(
                v.id, command.company_id,
                page=1, page_size=10000,
                status=ContractStatus.ACTIVE,
            )
            deps, dep_count = self.dependency_repo.find_all_by_vendor(
                v.id, command.company_id,
                page=1, page_size=10000,
            )
            critical_deps = sum(1 for d in deps if d.is_critical)

            rows.append({
                "vendor_name": v.name,
                "category": v.category.value if v.category else "",
                "is_active": v.is_active,
                "is_critical_ict": v.is_critical_ict,
                "risk_level": v.risk_level.value if v.risk_level else "unassessed",
                "contact_email": v.contact_email or "",
                "active_contracts": contract_count,
                "total_dependencies": dep_count,
                "critical_dependencies": critical_deps,
                "latest_assessment_date": (
                    str(latest.assessment_date) if latest else ""
                ),
                "next_review_date": (
                    str(latest.next_review_date)
                    if latest and latest.next_review_date
                    else ""
                ),
                "data_handling_score": latest.data_handling_score if latest else "",
                "security_certs_score": latest.security_certs_score if latest else "",
                "incident_response_score": latest.incident_response_score if latest else "",
                "business_continuity_score": latest.business_continuity_score if latest else "",
                "subcontractor_score": latest.subcontractor_score if latest else "",
                "overall_risk_level": (
                    latest.overall_risk_level.value if latest else ""
                ),
                "contracts": contracts,
            })

        if command.export_format == "csv":
            return self._generate_csv(rows)
        return self._generate_pdf(rows, command.company_id, today)

    @staticmethod
    def _generate_csv(rows: list[dict]) -> bytes:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Vendor",
            "Category",
            "Active",
            "Critical ICT",
            "Risk Level",
            "Contact Email",
            "Active Contracts",
            "Dependencies",
            "Critical Dependencies",
            "Last Assessment",
            "Next Review",
            "Data Handling",
            "Security Certs",
            "Incident Response",
            "Business Continuity",
            "Subcontractor",
            "Overall Risk",
        ])
        for r in rows:
            writer.writerow([
                r["vendor_name"],
                r["category"],
                "Yes" if r["is_active"] else "No",
                "Yes" if r["is_critical_ict"] else "No",
                r["risk_level"],
                r["contact_email"],
                r["active_contracts"],
                r["total_dependencies"],
                r["critical_dependencies"],
                r["latest_assessment_date"],
                r["next_review_date"],
                r["data_handling_score"],
                r["security_certs_score"],
                r["incident_response_score"],
                r["business_continuity_score"],
                r["subcontractor_score"],
                r["overall_risk_level"],
            ])
        return output.getvalue().encode("utf-8")

    @staticmethod
    def _generate_pdf(
        rows: list[dict], company_id: str, today: date,
    ) -> bytes:
        from core.config import settings

        env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
        env.globals["brand_name"] = settings.BRAND_NAME
        template = env.get_template("reports/vendor_risk_export.html")

        risk_counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        for r in rows:
            level = r["risk_level"]
            if level in risk_counts:
                risk_counts[level] += 1

        html_content = template.render(
            title="Vendor & Supply Chain Risk Report",
            company_id=company_id,
            generated_at=datetime.now(timezone.utc).strftime(
                "%Y-%m-%d %H:%M UTC",
            ),
            total_vendors=len(rows),
            active_vendors=sum(1 for r in rows if r["is_active"]),
            critical_ict=sum(1 for r in rows if r["is_critical_ict"]),
            risk_counts=risk_counts,
            vendors=rows,
        )

        try:
            from weasyprint import HTML as WeasyHTML
        except (ImportError, OSError) as exc:
            raise RuntimeError(
                "PDF generation unavailable: missing WeasyPrint system libraries.",
            ) from exc

        result: bytes = WeasyHTML(string=html_content).write_pdf()
        return result
