from dataclasses import dataclass
from typing import Optional

from src.audit_bc.audit.application.dtos import (
    ComplianceDashboardDto,
    ControlAssessmentDto,
    FrameworkSummaryDto,
)
from src.audit_bc.audit.domain.enums import ComplianceStatus
from src.audit_bc.audit.domain.repository import AuditRepositoryInterface
from src.framework.application.query_bus import Query, QueryHandler


@dataclass
class GetComplianceDashboardQuery(Query):
    company_id: str
    framework: Optional[str] = None


class GetComplianceDashboardQueryHandler(
    QueryHandler[GetComplianceDashboardQuery, ComplianceDashboardDto]
):
    def __init__(self, repo: AuditRepositoryInterface):
        self.repo = repo

    def handle(
        self, query: GetComplianceDashboardQuery
    ) -> ComplianceDashboardDto:
        controls = self.repo.find_controls(query.company_id)
        assessments = self.repo.find_assessments_by_company(
            query.company_id
        )
        evidence_counts = self.repo.count_evidence_by_control(
            query.company_id
        )

        assessment_map = {a.control_id: a for a in assessments}

        # Build per-control DTOs
        all_controls: list[ControlAssessmentDto] = []
        for c in controls:
            if query.framework and c.framework != query.framework:
                continue
            a = assessment_map.get(c.id)
            all_controls.append(
                ControlAssessmentDto(
                    control_id=c.id,
                    control_code=c.code,
                    control_name=c.name,
                    framework=c.framework,
                    description=c.description,
                    is_predefined=c.is_predefined,
                    status=(
                        a.status.value
                        if a
                        else ComplianceStatus.NOT_ASSESSED.value
                    ),
                    notes=a.notes if a else None,
                    assessed_by=a.assessed_by if a else None,
                    assessed_at=a.assessed_at if a else None,
                    evidence_count=evidence_counts.get(c.id, 0),
                )
            )

        total = len(all_controls)
        compliant = sum(
            1 for c in all_controls
            if c.status == ComplianceStatus.COMPLIANT.value
        )
        partial = sum(
            1 for c in all_controls
            if c.status == ComplianceStatus.PARTIAL.value
        )
        non_compliant = sum(
            1 for c in all_controls
            if c.status == ComplianceStatus.NON_COMPLIANT.value
        )
        not_assessed = sum(
            1 for c in all_controls
            if c.status == ComplianceStatus.NOT_ASSESSED.value
        )
        with_evidence = sum(
            1 for c in all_controls if c.evidence_count > 0
        )
        without_evidence = total - with_evidence

        overall_pct = (
            round(compliant / total * 100, 1) if total > 0 else 0.0
        )

        # Per-framework summaries
        frameworks: dict[str, list[ControlAssessmentDto]] = {}
        for ca in all_controls:
            frameworks.setdefault(ca.framework, []).append(ca)

        framework_summaries: list[FrameworkSummaryDto] = []
        for fw, fw_controls in sorted(frameworks.items()):
            fw_total = len(fw_controls)
            fw_compliant = sum(
                1 for c in fw_controls
                if c.status == ComplianceStatus.COMPLIANT.value
            )
            fw_partial = sum(
                1 for c in fw_controls
                if c.status == ComplianceStatus.PARTIAL.value
            )
            fw_non = sum(
                1 for c in fw_controls
                if c.status == ComplianceStatus.NON_COMPLIANT.value
            )
            fw_na = sum(
                1 for c in fw_controls
                if c.status == ComplianceStatus.NOT_ASSESSED.value
            )
            fw_with_ev = sum(
                1 for c in fw_controls if c.evidence_count > 0
            )
            framework_summaries.append(
                FrameworkSummaryDto(
                    framework=fw,
                    total_controls=fw_total,
                    compliant=fw_compliant,
                    partial=fw_partial,
                    non_compliant=fw_non,
                    not_assessed=fw_na,
                    compliance_pct=(
                        round(fw_compliant / fw_total * 100, 1)
                        if fw_total > 0
                        else 0.0
                    ),
                    evidence_coverage_pct=(
                        round(fw_with_ev / fw_total * 100, 1)
                        if fw_total > 0
                        else 0.0
                    ),
                )
            )

        # Gap controls: non_compliant + not_assessed
        gap_controls = [
            c for c in all_controls
            if c.status in (
                ComplianceStatus.NON_COMPLIANT.value,
                ComplianceStatus.NOT_ASSESSED.value,
            )
        ]

        return ComplianceDashboardDto(
            overall_compliance_pct=overall_pct,
            total_controls=total,
            compliant=compliant,
            partial=partial,
            non_compliant=non_compliant,
            not_assessed=not_assessed,
            controls_with_evidence=with_evidence,
            controls_without_evidence=without_evidence,
            frameworks=framework_summaries,
            gap_controls=gap_controls,
        )
