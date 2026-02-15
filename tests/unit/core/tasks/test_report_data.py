from unittest.mock import MagicMock, patch

from core.tasks.report_data import (
    collect_asset_inventory,
    collect_request_summary,
    collect_technician_performance,
)


class TestCollectAssetInventory:
    @patch("core.tasks.report_data.CompanyRepository")
    @patch("core.tasks.report_data.AssetRepository")
    def test_returns_expected_keys(self, MockAssetRepo, MockCompanyRepo):
        session = MagicMock()
        company = MagicMock()
        company.name = "Test Co"
        MockCompanyRepo.return_value.find_by_id.return_value = company
        MockAssetRepo.return_value.count_by_status.return_value = {"in_stock": 5, "assigned": 3}
        MockAssetRepo.return_value.count_by_type.return_value = {"laptop": 4, "monitor": 4}
        MockAssetRepo.return_value.find_all_by_company.return_value = []
        MockAssetRepo.return_value.find_expiring_warranties.return_value = []

        result = collect_asset_inventory("comp1", None, session)

        assert result["company_name"] == "Test Co"
        assert result["total_assets"] == 8
        assert "by_status" in result
        assert "by_type" in result
        assert "assets" in result
        assert "expiring_warranties" in result

    @patch("core.tasks.report_data.CompanyRepository")
    @patch("core.tasks.report_data.AssetRepository")
    def test_unknown_company(self, MockAssetRepo, MockCompanyRepo):
        session = MagicMock()
        MockCompanyRepo.return_value.find_by_id.return_value = None
        MockAssetRepo.return_value.count_by_status.return_value = {}
        MockAssetRepo.return_value.count_by_type.return_value = {}
        MockAssetRepo.return_value.find_all_by_company.return_value = []
        MockAssetRepo.return_value.find_expiring_warranties.return_value = []

        result = collect_asset_inventory("bad", None, session)
        assert result["company_name"] == "Unknown"


class TestCollectRequestSummary:
    @patch("core.tasks.report_data.CompanyRepository")
    @patch("core.tasks.report_data.RequestRepository")
    def test_returns_expected_keys(self, MockReqRepo, MockCompanyRepo):
        session = MagicMock()
        company = MagicMock()
        company.name = "Test Co"
        MockCompanyRepo.return_value.find_by_id.return_value = company
        MockReqRepo.return_value.count_by_status.return_value = {
            "submitted": 2, "in_review": 1, "in_progress": 3, "resolved": 10, "closed": 5,
        }
        MockReqRepo.return_value.count_by_type.return_value = {"incident": 10}
        MockReqRepo.return_value.count_by_priority.return_value = {"high": 5}
        MockReqRepo.return_value.avg_resolution_time.return_value = 12.5
        MockReqRepo.return_value.find_open_requests_with_age.return_value = []

        result = collect_request_summary("comp1", None, session)

        assert result["company_name"] == "Test Co"
        assert result["total_open"] == 6
        assert result["total_resolved"] == 10
        assert result["avg_resolution_time"] == 12.5
        assert "by_status" in result
        assert "by_type" in result
        assert "by_priority" in result

    @patch("core.tasks.report_data.CompanyRepository")
    @patch("core.tasks.report_data.RequestRepository")
    def test_with_date_range(self, MockReqRepo, MockCompanyRepo):
        session = MagicMock()
        MockCompanyRepo.return_value.find_by_id.return_value = MagicMock(name="Co")
        MockReqRepo.return_value.count_by_status.return_value = {}
        MockReqRepo.return_value.count_by_type.return_value = {}
        MockReqRepo.return_value.count_by_priority.return_value = {}
        MockReqRepo.return_value.avg_resolution_time.return_value = None
        MockReqRepo.return_value.find_open_requests_with_age.return_value = []

        result = collect_request_summary(
            "comp1", {"from_date": "2026-01-01", "to_date": "2026-01-31"}, session
        )
        assert result["date_range"] is not None
        assert result["date_range"]["from_date"] == "2026-01-01"


class TestCollectTechnicianPerformance:
    @patch("core.tasks.report_data.CompanyRepository")
    @patch("core.tasks.report_data.RequestRepository")
    def test_returns_expected_keys(self, MockReqRepo, MockCompanyRepo):
        session = MagicMock()
        company = MagicMock()
        company.name = "Test Co"
        MockCompanyRepo.return_value.find_by_id.return_value = company
        MockReqRepo.return_value.avg_resolution_time_by_technician.return_value = [
            {"technician_id": "t1", "avg_hours": 5.0, "resolved_count": 10},
        ]

        result = collect_technician_performance("comp1", None, session)

        assert result["company_name"] == "Test Co"
        assert len(result["by_technician"]) == 1
        assert result["by_technician"][0]["technician_id"] == "t1"

    @patch("core.tasks.report_data.CompanyRepository")
    @patch("core.tasks.report_data.RequestRepository")
    def test_empty_technicians(self, MockReqRepo, MockCompanyRepo):
        session = MagicMock()
        MockCompanyRepo.return_value.find_by_id.return_value = MagicMock(name="Co")
        MockReqRepo.return_value.avg_resolution_time_by_technician.return_value = []

        result = collect_technician_performance("comp1", None, session)
        assert result["by_technician"] == []
        assert result["date_range"] is None
