from unittest.mock import MagicMock, patch

from src.report_bc.report.domain.entities import Report
from src.report_bc.report.domain.enums import ReportStatus


def _make_report(**overrides):
    defaults = dict(company_id="comp1", requested_by="user1", type="asset_inventory")
    defaults.update(overrides)
    return Report.create(**defaults)


class TestGenerateReportTask:
    @patch("core.storage.S3StorageService")
    @patch("core.tasks.reports.HTML")
    @patch("core.tasks.reports._jinja_env")
    @patch("core.tasks.report_data.collect_asset_inventory")
    @patch("src.report_bc.report.infrastructure.repository.ReportRepository")
    @patch("core.database.SessionLocal")
    @patch("core.tasks.reports.generate_report.retry")
    def test_happy_path_completes(
        self, mock_retry, MockSession, MockRepo, mock_collector, mock_env, MockHTML, MockS3
    ):
        session = MagicMock()
        MockSession.return_value = session
        report = _make_report()
        repo_instance = MockRepo.return_value
        repo_instance.find_by_id_any_company.return_value = report

        mock_collector.return_value = {"company_name": "Test", "assets": [], "by_status": {}, "by_type": {}, "total_assets": 0, "expiring_warranties": []}
        mock_env.get_template.return_value.render.return_value = "<html></html>"
        MockHTML.return_value.write_pdf.return_value = b"%PDF"
        MockS3.return_value.upload.return_value = f"reports/comp1/{report.id}.pdf"

        from core.tasks.reports import generate_report
        generate_report(report.id)

        # Status updated to processing then completed
        calls = repo_instance.update_status.call_args_list
        assert calls[0].args[1] == ReportStatus.PROCESSING
        assert calls[1].args[1] == ReportStatus.COMPLETED
        assert "storage_key" in calls[1].kwargs

        # PDF generated and uploaded
        MockHTML.assert_called_once()
        MockS3.return_value.upload.assert_called_once()

    @patch("core.storage.S3StorageService")
    @patch("core.tasks.reports.HTML")
    @patch("core.tasks.reports._jinja_env")
    @patch("core.tasks.report_data.collect_asset_inventory")
    @patch("src.report_bc.report.infrastructure.repository.ReportRepository")
    @patch("core.database.SessionLocal")
    @patch("core.tasks.reports.generate_report.retry", side_effect=Exception("retry"))
    def test_failure_sets_failed_status(
        self, mock_retry, MockSession, MockRepo, mock_collector, mock_env, MockHTML, MockS3
    ):
        session = MagicMock()
        MockSession.return_value = session
        report = _make_report()
        repo_instance = MockRepo.return_value
        repo_instance.find_by_id_any_company.return_value = report

        mock_collector.side_effect = RuntimeError("data collection failed")

        from core.tasks.reports import generate_report

        try:
            generate_report(report.id)
        except Exception:
            pass

        # Should have set status to FAILED
        failed_call = [
            c for c in repo_instance.update_status.call_args_list
            if c.args[1] == ReportStatus.FAILED
        ]
        assert len(failed_call) == 1
        assert "error_message" in failed_call[0].kwargs

    @patch("src.report_bc.report.infrastructure.repository.ReportRepository")
    @patch("core.database.SessionLocal")
    def test_not_found_returns_early(self, MockSession, MockRepo):
        session = MagicMock()
        MockSession.return_value = session
        MockRepo.return_value.find_by_id_any_company.return_value = None

        from core.tasks.reports import generate_report
        generate_report("nonexistent")

        MockRepo.return_value.update_status.assert_not_called()

    @patch("core.storage.S3StorageService")
    @patch("core.tasks.reports.HTML")
    @patch("core.tasks.reports._jinja_env")
    @patch("core.tasks.report_data.collect_asset_inventory")
    @patch("src.report_bc.report.infrastructure.repository.ReportRepository")
    @patch("core.database.SessionLocal")
    @patch("core.tasks.reports.generate_report.retry")
    def test_s3_key_format(
        self, mock_retry, MockSession, MockRepo, mock_collector, mock_env, MockHTML, MockS3
    ):
        session = MagicMock()
        MockSession.return_value = session
        report = _make_report()
        repo_instance = MockRepo.return_value
        repo_instance.find_by_id_any_company.return_value = report

        mock_collector.return_value = {"company_name": "Test", "assets": [], "by_status": {}, "by_type": {}, "total_assets": 0, "expiring_warranties": []}
        mock_env.get_template.return_value.render.return_value = "<html></html>"
        MockHTML.return_value.write_pdf.return_value = b"%PDF"

        from core.tasks.reports import generate_report
        generate_report(report.id)

        upload_call = MockS3.return_value.upload.call_args
        key = upload_call.args[0]
        assert key == f"reports/{report.company_id}/{report.id}.pdf"

    @patch("src.notification_bc.notification.infrastructure.repository.NotificationRepository")
    @patch("core.storage.S3StorageService")
    @patch("core.tasks.reports.HTML")
    @patch("core.tasks.reports._jinja_env")
    @patch("core.tasks.report_data.collect_asset_inventory")
    @patch("src.report_bc.report.infrastructure.repository.ReportRepository")
    @patch("core.database.SessionLocal")
    @patch("core.tasks.reports.generate_report.retry")
    def test_notification_created_on_success(
        self, mock_retry, MockSession, MockRepo, mock_collector, mock_env, MockHTML, MockS3, MockNotifRepo
    ):
        session = MagicMock()
        MockSession.return_value = session
        report = _make_report()
        repo_instance = MockRepo.return_value
        repo_instance.find_by_id_any_company.return_value = report

        mock_collector.return_value = {"company_name": "Test", "assets": [], "by_status": {}, "by_type": {}, "total_assets": 0, "expiring_warranties": []}
        mock_env.get_template.return_value.render.return_value = "<html></html>"
        MockHTML.return_value.write_pdf.return_value = b"%PDF"
        MockS3.return_value.upload.return_value = "key"

        from core.tasks.reports import generate_report
        generate_report(report.id)

        # Notification should have been saved
        MockNotifRepo.return_value.save.assert_called_once()
        notif = MockNotifRepo.return_value.save.call_args.args[0]
        assert notif.user_id == report.requested_by
        assert notif.event_type == "report.ready"
        assert "report_id" in notif.data
        assert notif.title == "Report ready"
