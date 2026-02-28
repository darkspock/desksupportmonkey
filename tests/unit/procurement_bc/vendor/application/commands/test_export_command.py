from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from src.procurement_bc.vendor.application.commands.export_vendor_risk import (
    ExportVendorRiskCommand,
    ExportVendorRiskCommandHandler,
)
from src.procurement_bc.vendor.domain.entities import (
    Vendor,
    VendorContract,
    VendorRiskAssessment,
)
from src.procurement_bc.vendor.domain.enums import (
    ContractStatus,
    ContractType,
    VendorRiskLevel,
)

COMPANY = "comp01"


def _make_handler():
    vendor_repo = MagicMock()
    contract_repo = MagicMock()
    assessment_repo = MagicMock()
    dependency_repo = MagicMock()
    return (
        ExportVendorRiskCommandHandler(
            vendor_repo=vendor_repo,
            contract_repo=contract_repo,
            assessment_repo=assessment_repo,
            dependency_repo=dependency_repo,
        ),
        vendor_repo,
        contract_repo,
        assessment_repo,
        dependency_repo,
    )


class TestExportVendorRiskCommand:
    def test_csv_export_returns_bytes(self):
        handler, vendor_repo, contract_repo, assessment_repo, dep_repo = (
            _make_handler()
        )
        vendor = Vendor(
            id="v1",
            company_id=COMPANY,
            name="Acme Corp",
            is_active=True,
            is_critical_ict=True,
            risk_level=VendorRiskLevel.HIGH,
        )
        vendor_repo.find_all.return_value = ([vendor], 1)

        assessment = VendorRiskAssessment(
            id="a1",
            vendor_id="v1",
            company_id=COMPANY,
            assessed_by="user1",
            assessment_date=date(2026, 1, 15),
            data_handling_score=4,
            security_certs_score=3,
            incident_response_score=4,
            business_continuity_score=3,
            subcontractor_score=2,
            overall_risk_level=VendorRiskLevel.MEDIUM,
            next_review_date=date(2026, 7, 15),
        )
        assessment_repo.find_latest_by_vendor.return_value = assessment

        contract_repo.find_all_by_vendor.return_value = ([], 0)
        dep_repo.find_all_by_vendor.return_value = ([], 0)

        result = handler.handle(
            ExportVendorRiskCommand(
                company_id=COMPANY,
                export_format="csv",
                requested_by="admin1",
            ),
        )

        assert isinstance(result, bytes)
        csv_str = result.decode("utf-8")
        assert "Acme Corp" in csv_str
        assert "Yes" in csv_str  # is_critical_ict
        assert "high" in csv_str
        assert "2026-01-15" in csv_str
        # CSV header row
        assert "Vendor" in csv_str
        assert "Data Handling" in csv_str

    def test_csv_export_empty_company(self):
        handler, vendor_repo, contract_repo, assessment_repo, dep_repo = (
            _make_handler()
        )
        vendor_repo.find_all.return_value = ([], 0)

        result = handler.handle(
            ExportVendorRiskCommand(
                company_id=COMPANY,
                export_format="csv",
                requested_by="admin1",
            ),
        )

        assert isinstance(result, bytes)
        csv_str = result.decode("utf-8")
        lines = csv_str.strip().split("\n")
        assert len(lines) == 1  # Header only

    def test_csv_export_vendor_no_assessment(self):
        handler, vendor_repo, contract_repo, assessment_repo, dep_repo = (
            _make_handler()
        )
        vendor = Vendor(
            id="v1",
            company_id=COMPANY,
            name="New Vendor",
            is_active=True,
        )
        vendor_repo.find_all.return_value = ([vendor], 1)
        assessment_repo.find_latest_by_vendor.return_value = None
        contract_repo.find_all_by_vendor.return_value = ([], 0)
        dep_repo.find_all_by_vendor.return_value = ([], 0)

        result = handler.handle(
            ExportVendorRiskCommand(
                company_id=COMPANY,
                export_format="csv",
                requested_by="admin1",
            ),
        )

        csv_str = result.decode("utf-8")
        assert "New Vendor" in csv_str
        assert "unassessed" in csv_str
