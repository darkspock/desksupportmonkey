import logging
import os
from datetime import datetime, timezone

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

from core.celery import celery_app
from core.config import settings

logger = logging.getLogger(__name__)

TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "templates")

TEMPLATE_MAP = {
    "asset_inventory": "reports/asset_inventory.html",
    "request_summary": "reports/request_summary.html",
    "technician_performance": "reports/technician_performance.html",
}

_jinja_env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))


@celery_app.task(
    name="core.tasks.reports.generate_report",
    bind=True,
    max_retries=settings.report.REPORT_MAX_RETRIES,
)
def generate_report(self, report_id: str):
    """Generate a PDF report asynchronously."""
    from core.database import SessionLocal
    from core.storage import S3StorageService
    from core.tasks.report_data import (
        collect_asset_inventory,
        collect_request_summary,
        collect_technician_performance,
    )
    from src.report_bc.report.domain.enums import ReportStatus
    from src.report_bc.report.infrastructure.repository import ReportRepository

    DATA_COLLECTORS = {
        "asset_inventory": collect_asset_inventory,
        "request_summary": collect_request_summary,
        "technician_performance": collect_technician_performance,
    }

    session = SessionLocal()
    try:
        repo = ReportRepository(session)
        report = repo.find_by_id_any_company(report_id)
        if not report:
            logger.error("Report not found: %s", report_id)
            return

        # 1. Update status to processing
        repo.update_status(report_id, ReportStatus.PROCESSING)
        session.commit()

        # 2. Collect data
        collector = DATA_COLLECTORS[report.type.value]
        data = collector(report.company_id, report.parameters, session)

        # 3. Render HTML
        template_name = TEMPLATE_MAP[report.type.value]
        template = _jinja_env.get_template(template_name)
        html_content = template.render(
            title=report.type.value.replace("_", " ").title(),
            generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            **data,
        )

        # 4. Convert to PDF
        pdf_bytes = HTML(string=html_content).write_pdf()

        # 5. Upload to S3
        storage_key = f"reports/{report.company_id}/{report.id}.pdf"
        storage = S3StorageService()
        storage.upload(storage_key, pdf_bytes)

        # 6. Update report to completed
        repo.update_status(report_id, ReportStatus.COMPLETED, storage_key=storage_key)

        # 7. Create notification for the requester
        from src.notification_bc.notification.domain.entities import Notification
        from src.notification_bc.notification.domain.enums import EventType
        from src.notification_bc.notification.infrastructure.repository import NotificationRepository

        notif = Notification.create(
            user_id=report.requested_by,
            company_id=report.company_id,
            event_type=EventType.REPORT_READY.value,
            title="Report ready",
            body=f"{report.type.value.replace('_', ' ').title()} report is ready for download",
            data={"report_id": report.id},
        )
        notif_repo = NotificationRepository(session)
        notif_repo.save(notif)

        session.commit()
        logger.info("Report %s completed: %s", report_id, storage_key)

    except Exception as exc:
        session.rollback()
        try:
            repo.update_status(report_id, ReportStatus.FAILED, error_message=str(exc))
            session.commit()
        except Exception:
            session.rollback()
            logger.exception("Failed to update report status for %s", report_id)
        logger.exception("Report generation failed for %s", report_id)
        raise self.retry(exc=exc)
    finally:
        session.close()
