from unittest.mock import MagicMock, patch


class TestCollectSlaCompliance:
    def test_returns_expected_structure(self):
        session = MagicMock()
        params = {"from_date": "2026-01-01", "to_date": "2026-02-01"}

        mock_company = MagicMock()
        mock_company.name = "Acme Corp"

        mock_sla_repo = MagicMock()
        mock_sla_repo.compliance_stats.return_value = {
            "total_resolved": 50,
            "met": 40,
            "breached": 10,
            "compliance_pct": 80.0,
        }
        mock_sla_repo.compliance_by_priority.return_value = [
            {"priority": "high", "total": 20, "met": 15, "breached": 5, "compliance_pct": 75.0},
        ]
        mock_sla_repo.compliance_by_type.return_value = []
        mock_sla_repo.breach_trend.return_value = [
            {"period": "2026-01-06", "count": 3},
        ]

        with (
            patch(
                "core.tasks.report_data.CompanyRepository"
            ) as MockCompanyRepo,
            patch(
                "src.sla_bc.sla.infrastructure.repository.SlaRepository",
                return_value=mock_sla_repo,
            ),
        ):
            MockCompanyRepo.return_value.find_by_id.return_value = mock_company

            from core.tasks.report_data import collect_sla_compliance

            # Patch the SlaRepository class at import site
            with patch(
                "core.tasks.report_data.SlaRepository",
                create=True,
                return_value=mock_sla_repo,
            ):
                # Re-import to pick up the lazy import
                pass

        # Simpler approach: call with pre-patched module
        with (
            patch("core.tasks.report_data.CompanyRepository") as MockCompanyRepo,
        ):
            MockCompanyRepo.return_value.find_by_id.return_value = mock_company

            # The SlaRepository is imported lazily inside the function
            # We need to patch it at source
            with patch(
                "src.sla_bc.sla.infrastructure.repository.SlaRepository",
            ) as MockSlaRepoClass:
                MockSlaRepoClass.return_value = mock_sla_repo

                from core.tasks.report_data import collect_sla_compliance

                result = collect_sla_compliance("c1", params, session)

        assert result["company_name"] == "Acme Corp"
        assert result["total_resolved"] == 50
        assert result["met"] == 40
        assert result["breached"] == 10
        assert result["compliance_pct"] == 80.0
        assert len(result["by_priority"]) == 1
        assert len(result["breach_trend"]) == 1
        assert result["date_range"]["from_date"] == "2026-01-01"
        assert result["date_range"]["to_date"] == "2026-02-01"

    def test_defaults_to_last_30_days_when_no_dates(self):
        session = MagicMock()

        mock_company = MagicMock()
        mock_company.name = "TestCo"

        mock_sla_repo = MagicMock()
        mock_sla_repo.compliance_stats.return_value = {
            "total_resolved": 0, "met": 0, "breached": 0, "compliance_pct": 0.0,
        }
        mock_sla_repo.compliance_by_priority.return_value = []
        mock_sla_repo.compliance_by_type.return_value = []
        mock_sla_repo.breach_trend.return_value = []

        with (
            patch("core.tasks.report_data.CompanyRepository") as MockCompanyRepo,
            patch(
                "src.sla_bc.sla.infrastructure.repository.SlaRepository",
            ) as MockSlaRepoClass,
        ):
            MockCompanyRepo.return_value.find_by_id.return_value = mock_company
            MockSlaRepoClass.return_value = mock_sla_repo

            from core.tasks.report_data import collect_sla_compliance

            result = collect_sla_compliance("c1", None, session)

        assert "date_range" in result
        assert result["date_range"]["from_date"] is not None
        assert result["date_range"]["to_date"] is not None
